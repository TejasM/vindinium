#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import os
import pickle
import sys
import requests
from bot import RandomBot
import MultiNEAT as NEAT

TIMEOUT = 15


def get_new_game_state(session, server_url, key, mode='training', number_of_turns=10):
    """Get a JSON from the server containing the current state of the game"""

    if (mode == 'training'):
        # Don't pass the 'map' parameter if you want a random map
        params = {'key': key, 'turns': number_of_turns, 'map': 'm1'}
        api_endpoint = '/api/training'
    elif (mode == 'arena'):
        params = {'key': key}
        api_endpoint = '/api/arena'

    # Wait for 10 minutes
    r = session.post(server_url + api_endpoint, params, timeout=10 * 60)

    if (r.status_code == 200):
        return r.json()
    else:
        print("Error when creating the game")
        print(r.text)


def move(session, url, direction):
    """Send a move to the server
    
    Moves can be one of: 'Stay', 'North', 'South', 'East', 'West' 
    """

    try:
        r = session.post(url, {'dir': direction}, timeout=TIMEOUT)

        if (r.status_code == 200):
            return r.json()
        else:
            print("Error HTTP %d\n%s\n" % (r.status_code, r.text))
            return {'game': {'finished': True}}
    except requests.exceptions.RequestException as e:
        print(e)
        return {'game': {'finished': True}}


def is_finished(state):
    return state['game']['finished']


def start(server_url, key, mode, turns, bot):
    """Starts a game with all the required parameters"""

    # Create a requests session that will be used throughout the game
    session = requests.session()

    if (mode == 'arena'):
        print(u'Connected and waiting for other players to join…')
    # Get the initial state
    state = get_new_game_state(session, server_url, key, mode, turns)
    print("Playing at: " + state['viewUrl'])

    while not is_finished(state):
        # Some nice output ;)
        sys.stdout.write('.')
        sys.stdout.flush()

        # Choose a move
        direction = bot.move(state)

        # Send the move and receive the updated game state
        url = state['playUrl']
        state = move(session, url, direction)

    # Clean up the session
    session.close()
    return bot.hero.gold


if __name__ == "__main__":
    if (len(sys.argv) < 4):
        print("Usage: %s <key> <[training|arena]> <number-of-games|number-of-turns> [server-url]" % (sys.argv[0]))
        print('Example: %s mySecretKey training 20' % (sys.argv[0]))
    else:
        key = sys.argv[1]
        mode = sys.argv[2]

        if (mode == "training"):
            number_of_games = 10
            number_of_turns = int(sys.argv[3])
        else:
            number_of_games = int(sys.argv[3])
            number_of_turns = 300  # Ignored in arena mode

        if (len(sys.argv) == 5):
            server_url = sys.argv[4]
        else:
            server_url = "http://vindinium.org"
        params = NEAT.Parameters()
        params.PopulationSize = 50
        params.DynamicCompatibility = True
        params.AllowClones = True
        params.CompatTreshold = 5.0
        params.CompatTresholdModifier = 0.3
        params.YoungAgeTreshold = 15
        params.SpeciesMaxStagnation = 25
        params.OldAgeTreshold = 35
        params.MinSpecies = 3
        params.MaxSpecies = 10
        params.RouletteWheelSelection = True
        params.RecurrentProb = 0.25
        params.OverallMutationRate = 0.33
        params.MutateWeightsProb = 0.90
        params.WeightMutationMaxPower = 1.0
        params.WeightReplacementMaxPower = 5.0
        params.MutateWeightsSevereProb = 0.5
        params.WeightMutationRate = 0.75
        params.MaxWeight = 20
        params.MutateAddNeuronProb = 0.01
        params.MutateAddLinkProb = 0.05
        params.MutateRemLinkProb = 0.00

        genome = NEAT.Genome(0, 13, 0, 5, False, NEAT.ActivationFunction.TANH,
                             NEAT.ActivationFunction.UNSIGNED_SIGMOID, 0, params)
        best_genome_ever = None
        pop = NEAT.Population(genome, params, True, 1.0)
        top_score = 200
        top_pop_score = 0
        for generation in range(100):
            genome_list = NEAT.GetGenomeList(pop)
            for i, genome in enumerate(genome_list):
                net = NEAT.NeuralNetwork()
                genome.BuildPhenotype(net)

                score = start(server_url, key, mode, number_of_turns, RandomBot(net))
                genome.SetFitness(score / top_score)
                print score
                if top_pop_score < score / top_score:
                    top_pop_score = score / top_score
                print("\nGame finished: %d/%d" % (i + 1, len(genome_list)))

            best = max([x.GetLeader().GetFitness() for x in pop.Species])
            print 'Best fitness:', best, 'Species:', len(pop.Species)

            # Draw the best genome's phenotype
            net = NEAT.NeuralNetwork()
            best_genome_ever = pop.Species[0].GetLeader()
            best_genome_ever.BuildPhenotype(net)
            pickle.dump((best_genome_ever, net), open('best-' + str(generation)))
            pop.Epoch()

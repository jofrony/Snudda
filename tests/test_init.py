import unittest
import os
import numpy as np

from snudda.init import SnuddaInit


class TestInit(unittest.TestCase):

    def setUp(self):

        if os.path.dirname(__file__):
            os.chdir(os.path.dirname(__file__))

    def test_init(self):
        
        with self.subTest(stage="init_cube"):

            network_path = os.path.join(os.path.dirname(__file__), "tests", "network_testing_init_cube")
    
            config_name = os.path.join(network_path, "network-config.json")
            cnc = SnuddaInit(struct_def={}, config_file=config_name, num_population_units=2,
                             population_unit_centres="np.array([[3009, 4114, 4550], [4070, 5175, 5611]])*1e-6",
                             population_unit_radius=1400)
            cnc.define_striatum(num_dSPN=47500, num_iSPN=47500, num_FS=1300, num_LTS=0, num_ChIN=0,
                                volume_type="cube")
            cnc.write_json(config_name)

            # TODO: This only checks that the code runs. Add check for output

        with self.subTest(stage="init_slice"):
            network_path = os.path.join(os.path.dirname(__file__), "tests", "network_testing_init_slice")

            config_name = os.path.join(network_path, "network-config.json")
            cnc = SnuddaInit(struct_def={}, config_file=config_name, num_population_units=1)
            cnc.define_striatum(num_dSPN=47500, num_iSPN=47500, num_FS=1300, num_LTS=0, num_ChIN=0,
                                volume_type="slice")
            cnc.write_json(config_name)
            
        with self.subTest(stage="init_full"):
            network_path = os.path.join(os.path.dirname(__file__), "tests", "network_testing_init_full")

            config_name = os.path.join(network_path, "network-config.json")
            cnc = SnuddaInit(struct_def={}, config_file=config_name, num_population_units=1)
            cnc.define_striatum(num_neurons=1670000)
            cnc.write_json(config_name)

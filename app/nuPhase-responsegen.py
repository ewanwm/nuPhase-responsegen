import sys
import argparse
import typing
from tqdm import tqdm
import cerberus
import yaml
import pickle

import matplotlib.pyplot as plt

from nuphaserg.neut import NReWeight, make_reweight_instance, NeutReader

class Dial:

    def __init__(
        self,
        name: str,
        sigma: float,
        response_function_values: typing.List[float]
    ):

        self.name: str = name
        self.sigma: float = sigma
        self.response_function_values: typing.List[float] = response_function_values

class ReweightConfig:

    parameter_schema = {
        "name": {
            "type": "string"
        },
        "values": {
            "type": "list", 
            "schema": {
                "type": "float"
            }
        },
        "value_type": {
            "type": "string",
            "allowed": ["absolute", "tweak", "tweak_sigma"],
        }
    }
    
    schema: typing.Dict = {
        "parameters": {
            "type": "list",
            "schema": {
                "type" : "dict", 
                "schema": parameter_schema
            }
        }
    }

    def __init__(self, yaml_config: str, reweight_instance: NReWeight, validate: bool = False):

        self.reweight_instance: NReWeight = reweight_instance

        self.validator: 'cerberus.Validator' = cerberus.Validator(ReweightConfig.schema)
    
        self.yaml_config = None

        self.parameters = None

        self.yaml_config = yaml_config

        if validate:

            if self.reweight_instance is None:
            
                raise ValueError("No neut reweight instance provided, can't validate!")
            
            if not (self.validate_config(self.yaml_config)):

                raise ValueError("Bad config!")

        self.parse_config(self.yaml_config)

    def validate_config(self, config: typing.Dict) -> bool:

        is_valid = self.validator.validate(config)
        print(self.validator.errors)
        
        ## check that all mentioned dials are dealt with by neut reweight
        for parameter_yaml in self.yaml_config["parameters"]:
        
            param_name = parameter_yaml["name"]
            if not self.reweight_instance.dial_is_handled(param_name):
                print(f"ERROR: parameter {param_name} is not known to neut reweight!")
                
                is_valid = False

        return is_valid
                
    def parse_config(self, config: typing.Dict) -> None:

        self.parameters = []

        for parameter_yaml in self.yaml_config["parameters"]:

            param_name = parameter_yaml["name"]
            param_sigma = self.reweight_instance.get_dial_sigma(param_name)
            generated_value = self.reweight_instance.get_dial_generated(param_name)

            ## get the parameter tweak values
            raw_param_values = parameter_yaml["values"]
            param_values = []
            tweak_type = parameter_yaml["value_type"]
            if tweak_type == "absolute":
                param_values = raw_param_values
            
            elif tweak_type == "tweak":
                for val in raw_param_values:
                    param_values.append(generated_value + val)
            
            elif tweak_type == "tweak_sigma":
                for val in raw_param_values:
                    param_values.append(generated_value + val * param_sigma)

            else:
                raise ValueError("?????")
            
            dial = Dial(
                name = param_name,
                sigma = param_sigma,
                response_function_values = param_values
            )

            self.parameters.append(dial)

def setup_parser():
    ## set up subcommand parsers
    parser = argparse.ArgumentParser("nuPhase-responsegen")
    subparsers = parser.add_subparsers(title = "Commands", required=True, dest="command")

    ## set up response function maker command
    make_response_fn_parser = subparsers.add_parser("make-response-functions", help="Make response functions by evaluating neut reweight engine for dials at specified values")
    make_response_fn_parser.set_defaults(func = make_response_functions)
    make_response_fn_parser.add_argument("--input", "-i", type = str, required=True, help = "The input file containing the neut vectors")
    make_response_fn_parser.add_argument("--neut-card", type = str, required=True, help = "The path to the neut card that was used to generate the input file")
    make_response_fn_parser.add_argument("--config", "-c", type = str, required=True, help = "Path to the yaml file describing the response function reweighting to apply")
    make_response_fn_parser.add_argument("--output-file", "-o", type = str, required=True, help = "Path to output file")
    make_response_fn_parser.add_argument("--max-n-entries", "-n", type = int, required=False, default=None, help = "Maximum number of entries to read from the file, if not specified then all will be read")

    ## set up response function maker command
    plot_response_fn_parser = subparsers.add_parser("plot-response-functions", help="Make plots of response functions for debugging and illustration")
    plot_response_fn_parser.set_defaults(func = plot_response_functions)
    plot_response_fn_parser.add_argument("--input", "-i", type = str, required=True, help = "The input file containing the response functions")
    plot_response_fn_parser.add_argument("--neut-card", type = str, required=True, help = "The path to the neut card that was used to generate the input file")
    plot_response_fn_parser.add_argument("--output-file", "-o", type = str, required=True, help = "Path to output file")
    plot_response_fn_parser.add_argument("--max-n-entries", "-n", type = int, required=False, default=None, help = "Maximum number of entries to read from the file, if not specified then all will be read")

    return parser

def plot_response_functions(args):

    ## initialise global neut stuff
    neut.initialise(args.neut_card)

    ## create an instance of the reweight engine
    rw_inst = make_reweight_instance()

    with open(args.input, "rb") as file:

        unpickler = pickle.Unpickler(file)
        data = unpickler.load()

    config = ReweightConfig(data["config"], rw_inst)

    for parameter in config.parameters:

        parameter_values = parameter.response_function_values

        plt.clf()

        for event_weights in data["weights"]:

            if event_weights[parameter.name] is not None:

                plt.plot(parameter_values, event_weights[parameter.name], c = "k", alpha = 0.01)

        plt.savefig(f"{parameter.name}.png")

def make_response_functions(args):

    ## initialise global neut stuff
    initialise(args.neut_card)

    ## initialise the neut file reader
    reader = NeutReader(args.input)

    ## create an instance of the reweight engine
    rw_inst = make_reweight_instance()

    ## set up the reweight config instance
    config = None
    with open(args.config, "r") as config_file:
        yaml_config = yaml.safe_load(config_file)
        config = ReweightConfig(yaml_config=yaml_config, validate=True, reweight_instance=rw_inst)

    print(f"N entries: {reader.get_entries()}")

    ## only read specified number of entries (if specified)
    max_n_events = reader.get_entries()
    if args.max_n_entries is not None:
        max_n_events = min(args.max_n_entries, max_n_events)

    print(f"  - Reading {max_n_events}")

    data = {
        "config": config.yaml_config,
        "weights": []
    }

    for entry in tqdm(range(0, max_n_events), "Entry"):

        reader.get_entry(entry)

        weight_dict = {}
        for parameter in config.parameters:

            weights = []
            for value in parameter.response_function_values:

                rw_inst.set_dial(parameter.name, value)
                rw_inst.reconfigure()

                weight = rw_inst.calc_weight()
                rw_inst.reset()

                weights.append(weight)

            ## if all the weights are 1, save None instead
            if all([val == 1.0 for val in weights]):
                weights = None

            weight_dict[parameter.name] = weights

        data["weights"].append(weight_dict)

    with open(args.output_file, "wb") as file:

        pickler = pickle.Pickler(file)
        pickler.dump(data)

def main():

    parser = setup_parser()

    ## parse args
    args = parser.parse_args(sys.argv[1:])

    ## run the relevant function
    args.func(args)

if __name__ == "__main__":
    main()
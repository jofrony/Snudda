# python3 plot_traces.py save/traces/network-voltage-0.csv save/network-connect-synapse-file-0.hdf5


import sys
import os

import h5py
import numpy as np
from snudda.utils.load import SnuddaLoad
from snudda.utils.load_network_simulation import SnuddaLoadNetworkSimulation
import re
import ntpath
import time


class PlotTraces:

    ############################################################################

    def __init__(self, file_name, network_file=None, input_file=None):

        self.file_name = file_name
        self.network_file = network_file
        self.input_file = input_file

        self.time = []
        self.voltage = dict([])

        self.neuron_name_remap = {"FSN": "FS"}

        # self.read_csv()

        try:
            self.ID = int(re.findall('\d+', ntpath.basename(file_name))[0])
        except:
            print("Unable to guess ID, using 666.")
            self.ID = 666

        if network_file is None and "simulation" in file_name:
            network_path = os.path.dirname(os.path.dirname(file_name))
            network_file = os.path.join(network_path, "network-synapses.hdf5")
            if os.path.exists(network_file):
                self.network_file = network_file

        if network_file is not None:
            network_path = os.path.dirname(os.path.dirname(network_file))
        else:
            network_path = None

        if self.network_file is not None:
            self.network_info = SnuddaLoad(self.network_file)
            # assert(int(self.ID) == int(self.networkInfo.data["SlurmID"]))

        else:
            self.network_info = None

        if self.input_file is not None:
            self.input_info = h5py.File(self.input_file, "r")
        else:
            self.input_info = None

        self.output_load = SnuddaLoadNetworkSimulation(network_simulation_output_file=file_name,
                                                       network_path=network_path)

        self.voltage, self.time = self.output_load.get_voltage()

    ############################################################################

    def read_csv(self):

        assert False, "read_csv is deprecated, use SnuddaLoadNetworkSimulation instead"

        data = np.genfromtxt(self.file_name, delimiter=',')

        assert (data[0, 0] == -1)  # First column should be time

        self.time = data[0, 1:] / 1e3

        self.voltage = dict()

        for rows in data[1:, :]:
            c_id = int(rows[0])
            self.voltage[c_id] = rows[1:] * 1e-3

    ############################################################################

    def neuron_name(self, neuron_type):

        if neuron_type in self.neuron_name_remap:
            return self.neuron_name_remap[neuron_type]
        else:
            return neuron_type

    ############################################################################

    def plot_traces(self, trace_id=None, offset=150e-3, colours=None, skip_time=None,
                    title=None, fig_name=None):

        if skip_time is not None:
            print(f"!!! Excluding first {skip_time} s from the plot")

        if not trace_id:
            if self.network_info:
                trace_id = [x["neuronID"] for x in self.network_info.data["neurons"]]
            else:
                trace_id = [x for x in self.voltage]
        elif isinstance(trace_id, (int, np.integer)):
            trace_id = [trace_id]

        if colours is None:
            colours = {"dSPN": (77. / 255, 151. / 255, 1.0),
                       "iSPN": (67. / 255, 55. / 255, 181. / 255),
                       "FS": (6. / 255, 31. / 255, 85. / 255),
                       "ChIN": [252. / 255, 102. / 255, 0],
                       "LTS": [150. / 255, 63. / 255, 212. / 255]}

        print(f"Plotting traces: {trace_id}")
        print(f"Plotted {len(trace_id)} traces (total {len(self.voltage)})")

        import matplotlib.pyplot as plt

        types_in_plot = set()

        if self.network_info is not None:
            cell_types = [n["type"] for n in self.network_info.data["neurons"]]
            cell_id_check = [n["neuronID"] for n in self.network_info.data["neurons"]]
            try:
                assert (np.array([cell_id_check[x] == x for x in trace_id])).all(), \
                    "Internal error, assume IDs ordered"
            except:
                import traceback
                tstr = traceback.format_exc()
                print(tstr)
                print("This is strange...")
                import pdb
                pdb.set_trace()

            cols = [colours[c] if c in colours else [0, 0, 0] for c in cell_types]

        fig = plt.figure()

        ofs = 0

        if skip_time is not None:
            time_idx = np.where(self.time >= skip_time)[0]
        else:
            skip_time = 0.0
            time_idx = range(0, len(self.time))

        plot_count = 0

        for r in trace_id:

            if r not in self.voltage:
                print("Missing data for trace " + str(r))
                continue

            plot_count += 1
            types_in_plot.add(self.network_info.data["neurons"][r]["type"])

            if colours is None or self.network_info is None:
                colour = "black"
            else:
                try:
                    colour = cols[r]
                except:
                    import traceback
                    tstr = traceback.format_exc()
                    print(tstr)
                    import pdb
                    pdb.set_trace()

            plt.plot(self.time[time_idx] - skip_time,
                     self.voltage[r][time_idx] + ofs,
                     color=colour)

            if offset:
                ofs += offset

        if plot_count == 0:
            plt.close()
            return

        plt.xlabel('Time')
        plt.ylabel('Voltage')

        if title is None and self.input_info is not None and len(trace_id) == 1:
            n_inputs = 0
            for input_type in self.input_info["input"][str(trace_id[0])]:
                n_inputs += self.input_info["input"][str(trace_id[0])][input_type]["spikes"].shape[0]

            title = f"{self.network_info.data['neurons'][trace_id[0]]['name']} receiving {n_inputs} inputs"

        if title is not None:
            plt.title(title)

        if offset != 0:
            ax = fig.axes[0]
            ax.set_yticklabels([])

        plt.tight_layout()

        # plt.savefig('figures/Network-spikes-' + str(self.ID) + "-colour.pdf")

        fig_path = os.path.join(os.path.dirname(os.path.realpath(self.network_file)), "figures")
        if not os.path.exists(fig_path):
            os.makedirs(fig_path)

        if fig_name is None:
            if len(types_in_plot) > 1:
                fig_name = f"Network-voltage-trace-{self.ID}-{'-'.join(types_in_plot)}-colour.pdf"
            else:
                fig_name = f"Network-voltage-trace-{self.ID}-{types_in_plot.pop()}-colour.pdf"

        plt.savefig(os.path.join(fig_path, fig_name), dpi=300)
        print(f"Saving to figure {fig_name}")

        plt.ion()
        plt.show()
        # plt.draw()
        plt.pause(0.5)  # Show interactive plot (that user can interact with for a short period of time)

        return fig

    ############################################################################

    def plot_trace_neuron_name(self, neuron_name, num_traces=1, skip_time=0, plot_offset=0, fig_name=None, num_offset=0):

        assert self.network_info is not None, "You need to specify networkInfo file"

        neuron_names = [x["name"] for x in self.network_info.data["neurons"]]
        traceID = [x[0] for x in enumerate(neuron_names) if x[1].lower() == neuron_name.lower()]

        num_traces = min(len(traceID), num_traces)

        if num_traces <= 0:
            print("No traces of neuron(s) " + str(neuron_name) + " to show")
            return

        fig = self.plot_traces(offset=plot_offset, trace_id=traceID[num_offset:num_offset + num_traces],
                               skip_time=skip_time,
                               title=neuron_names[traceID[0]], fig_name=fig_name)

        time.sleep(1)
        return fig

    ############################################################################

    def plot_trace_neuron_type(self, neuron_type, num_traces=10, offset=0, skip_time=0.0):

        assert self.network_info is not None, "You need to specify networkInfo file"

        neuron_types = [x["type"] for x in self.network_info.data["neurons"]]

        # Find numbers of the relevant neurons

        trace_id = [x[0] for x in enumerate(neuron_types) if x[1].lower() == neuron_type.lower()]

        num_traces = min(len(trace_id), num_traces)

        if num_traces <= 0:
            print(f"No traces of {neuron_type} to show")
            return

        fig = self.plot_traces(offset=offset, trace_id=trace_id[:num_traces], skip_time=skip_time,
                               title=self.neuron_name(neuron_type))

        time.sleep(1)
        return fig

    ############################################################################


if __name__ == "__main__":

    # TODO: Update to use argparser

    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = None

    if len(sys.argv) > 2:
        network_file = sys.argv[2]
    else:
        network_file = None

    if file_name is not None:
        npt = PlotTraces(file_name, network_file)
        # npt.plotTraces(offset=0.2,traceID=[17,40,11,18])
        # npt.plotTraces(offset=0.2,traceID=[0,1,2,3,4,5,6,7,8,9])
        # npt.plotTraces(offset=0,traceID=[0,1,2,3,4,5,6,7,8,9])
        # npt.plotTraces(offset=0,traceID=[0,5,55]) #,5,55])
        # npt.plotTraces(offset=0,traceID=np.arange(0,100)) #,5,55])
        # npt.plotTraces(offset=-0.2,traceID=np.arange(0,20),skipTime=0.5)
        # npt.plotTraces(offset=-0.2,traceID=[5,54],skipTime=0.5)
        # npt.plotTraces(offset=0.2,traceID=[1,5,7,15,16],skipTime=0.2)

        plot_offset = 0  # -0.2
        skip_time = 0  # 0.5
        num_traces_max = 10

        if True:
            npt.plot_trace_neuron_type(neuron_type="dSPN", num_traces=num_traces_max, offset=plot_offset, skip_time=skip_time)
            npt.plot_trace_neuron_type(neuron_type="iSPN", num_traces=num_traces_max, offset=plot_offset, skip_time=skip_time)
            npt.plot_trace_neuron_type(neuron_type="FS", num_traces=num_traces_max, offset=plot_offset, skip_time=skip_time)
            npt.plot_trace_neuron_type(neuron_type="LTS", num_traces=num_traces_max, offset=plot_offset, skip_time=skip_time)
            npt.plot_trace_neuron_type(neuron_type="ChIN", num_traces=num_traces_max, offset=plot_offset, skip_time=skip_time)

        if False:
            npt.plot_trace_neuron_name(neuron_name="FS_0", plot_offset=plot_offset, fig_name="Traced-FS_0.pdf",
                                       num_offset=10)
            npt.plot_trace_neuron_name(neuron_name="FS_1", plot_offset=plot_offset, fig_name="Traced-FS_1.pdf")
            npt.plot_trace_neuron_name(neuron_name="FS_2", plot_offset=plot_offset, fig_name="Traced-FS_2.pdf")
            npt.plot_trace_neuron_name(neuron_name="FS_3", plot_offset=plot_offset, fig_name="Traced-FS_3.pdf")

    else:
        print(f"Usage: {sys.argv[0]} network-voltage-XXX.csv my_network/network-synapses.hdf5")

#  TODO: Need to clean up the code and make a new plot function

# import pdb
# pdb.set_trace()

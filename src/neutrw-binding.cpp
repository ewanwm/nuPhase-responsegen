#include "CommonBlockIFace.h"
#include "NReWeightFactory.h"

#include "NEUTROOTReader.h"
#include "neutvect.h"

#include "TFile.h"
#include "TTree.h"

#include "nework.h"
#include "posinnuc.h"
#include "vcwork.h"

#include <fstream>
#include <string.h>

#include <pybind11/pybind11.h>

namespace py = pybind11;

///@brief Simple helper class to aid in reading events into neut
class NeutReader
{

  public:
    NeutReader(const std::string &inputFileName)
    :
        inputFile(nullptr),
        neutVectorTree(nullptr),
        currentNeutVect(nullptr),
        nEntries(0)
    {
        // check the path to the file is valid
        std::ifstream input(inputFileName);
        if (!input.is_open()) {
            throw std::runtime_error(inputFileName + " could not be opened for reading");
        }
        input.close();

        // read the input file
        inputFile = TFile::Open(inputFileName.c_str(), "READ");
        neutVectorTree = inputFile->Get<TTree>("neuttree");
        
        if (!neutVectorTree)
        {
            throw std::runtime_error("Error opening file " + inputFileName + " does not contain 'neuttree' tree");
        }

        // set branch address of vector object
        neutVectorTree->SetBranchAddress("vectorbranch", &currentNeutVect);
        nEntries = neutVectorTree->GetEntries();
    }

    ///@brief Read a particular entry from the input tree
    ///
    ///Returns true if the entry was read successfully, false otherwise
    bool getEntry(size_t eventId)
    {
        // if user asked for entry past end of list
        if(eventId > nEntries)
        {
            return false;
        }

        // get the entry
        neutVectorTree->GetEntry(eventId);

        // set awful awful global event 
        NEUTROOT::ReadEvent(currentNeutVect);

        return true;
    }

    ///@brief Get the number of entries present in the neut tree
    inline size_t getEntries() const
    {
        return nEntries;
    }

  private:
    TFile *inputFile;
    TTree *neutVectorTree;
    NeutVect *currentNeutVect;
    size_t nEntries;

};

PYBIND11_MODULE(neut, m)
{

    m.doc() = 
        "This module provides a very lightweight python wrapper around NEUTs reweighting tools"
        ""
        "Typical usage would look something like"
        ""
        ".. code:: python"
        ""
        "    input_file = <path to some input neut file>"
        "    neut_card = <path to neut card used to generate the input file>"
        ""
        "    initialise(neut_card)"
        "    reader = NeutReader(input_file_name = input_file)"
        "    reweighter = make_reweight_instance()"
        ""
        "    for entry in range(reader.get_entries()):"
        ""
        "        ## do "
        "        ## some"
        "        ## stuff"
        "        ## with"
        "        ## reweighter"
        ""
        ".. warning:: "
        ""
        "    The `initialise(neut_card=...)` must be called before doing anything else NEUT related"
        ""
    ;

    py::class_<NeutReader>(m, "NeutReader", py::buffer_protocol())
        .def(py::init<const std::string&>(), py::arg("input_file_name"))
        .def("get_entries", &NeutReader::getEntries, "Get the number of entries in the file")
        .def("get_entry", &NeutReader::getEntry, "Read a particular entry for the file - this will alter the global neut state to load the specified 'event' as the current one")
        .doc() = 
            "Simple helper class to aid in reading events from a neut file"
            ""
            "Neut uses global variables when reading events so any event loaded by this class becomes *THE* current neut event"
            ""
            ".. warning::"
            "    "
            "    You should only ever have one NeutReader 'active' at a given time"
            ""
    ;

    m.def("initialise", [](const std::string &cardFile) -> void
        {
            neut::CommonBlockIFace::Initialize(cardFile.c_str());        
        },
        "Initialises NEUT related global things. This *must* be called before doing anything else Neut related",
        py::arg("card_file")
    )
    ;

    py::class_<neut::rew::NReWeight>(m, "NReWeight")
        .def(py::init())
        .def("calc_weight", &neut::rew::NReWeight::CalcWeight, "Calculate a weight for the current event given all currently configured dial values")
        .def("reconfigure", &neut::rew::NReWeight::Reconfigure, "Registers any dial values that have been set. Should be called after all calls to set_dial_value() and before call to calc_weight()")
        .def("get_dial_generated", [](neut::rew::NReWeight &self, const std::string &dialName) -> float
            {
                neut::NSyst_t index = self.DialFromString(dialName);
                return self.GetDial_From_Value(index);
            },
            "Get the value of the dial that was used to generate the current neut file", py::arg("dial_name")
        )
        .def("set_dial", [](neut::rew::NReWeight &self, const std::string &dialName, float dialValue) -> void
            {
                neut::NSyst_t index = self.DialFromString(dialName);
                self.SetDial_To_Value(index, dialValue);
            },
            "Set a dial to some value",
            py::arg("dial_name"), py::arg("dial_value")
        )
        .def("dial_is_handled", [](neut::rew::NReWeight &self, const std::string &dialName) -> bool
            {
                return self.DialIsHandled(dialName);
            },
            "Check if a dial is handled by one of NEUTs reweighting engines",
            py::arg("dial_name")
        )
        .def("get_dial_sigma", [](neut::rew::NReWeight &self, const std::string &dialName) -> float
            {
                neut::NSyst_t index = self.DialFromString(dialName);
                return self.GetDial_OneSigma(index, 1.0);
            },
            "Get the NEUT one sigma uncertainty for a dial",
            py::arg("dial_name")
        )
        .def("reset", &neut::rew::NReWeight::Reset, "Reset dial values. You will probably want to call this after calc_weight() and before setting any new dial values")
        .doc() = 
            "Handles reweighting. Should be accessed via the make_reweight_instance() function"
            ""
            "Usage would look something like"
            ""
            ".. code:: python"
            ""
            "    initialise(<card file>)"
            "    reader = NeutReader(<neut file>)"
            "    reader.get_entry(0)"
            ""
            "    ## this is the NReWeight instance"
            "    reweighter = make_reweight_instance()"
            ""
            "    for dial_name in <list of dial names>:"
            ""
            "        ## check that the dial is actually handled by some reweight engine"
            "        assert reweighter.dial_is_handled(dial_name)"
            ""
            "        for value in <list of dial values>:"
            ""
            "            ## set the dial to some value"
            "            reweighter.set_dial(dial, value)"
            ""
            "            ## registers any changes to dials"
            "            reweighter.reconfigure()"
            ""
            "            weight = reweighter.calc_weight()"
            ""
            "            print(weight)"
            ""
            "            ## resets any changes to dials"
            "            reweighter.reset()"
            ""
            ".. note:: The call to reconfigure() *before* calc_weight() and the call to reset() *after*"
            ""
    ;

    m.def("make_reweight_instance", &neut::rew::MakeNReWeightInstance).doc() = "Creates a NReWeight instance that can be used to apply reweights to the currenly loaded event";

}

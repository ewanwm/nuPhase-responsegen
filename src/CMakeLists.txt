pybind11_add_module(neut MODULE neutrw-binding.cpp)

target_link_libraries(neut PUBLIC NEUT::All ROOT::Core ROOT::Physics ROOT::Tree)
target_include_directories(neut PRIVATE ${NEUT_INCLUDE_DIR})

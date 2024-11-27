CC = g++
CCFLAGS = -std=c++17 -pthread
BOOST = ~/boost_1_82_0/boost


HELPER_FILES = setup_helpers.hpp graph_helpers.hpp

main: main.cpp $(HELPER_FILES)
	$(CC) $(CCFLAGS) $< -o $@

node: node.cpp $(HELPER_FILES)
	$(CC) $(CCFLAGS) $< -o $@

sample: testgraph.cpp
	$(CC) $(CCFLAGS) $< -o $@ -I $(BOOST)


.PHONY: clean

clean: 
	rm -rf *.o




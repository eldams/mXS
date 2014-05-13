#DEBUG OPT=-Wno-deprecated -g -O0
OPT=-Wno-deprecated -O3
CC=g++
OUT=bin/sminer
SOURCE=src/
BUILD=build/

$(OUT): $(SOURCE)main.cpp $(BUILD)Dataset.o $(BUILD)Miner.o $(BUILD)Node.o
	@echo "Compiling $@"
	@$(CC) $(SOURCE)main.cpp $(BUILD)Dataset.o $(BUILD)Miner.o $(BUILD)Node.o -o $(OUT) $(OPT)
$(BUILD)%.o: $(SOURCE)%.cpp
	@echo "Building $<"
	$(CC) -c $< -o $@ $(OPT)

clean:
	@echo "Cleaning!"
	@rm -f $(BUILD)*.o
	@rm -f $(OUT)


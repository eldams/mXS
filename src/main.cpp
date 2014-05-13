#include <iostream>
#include <cstring>
#include <stdlib.h>
#include "global.h"
#include "Dataset.h"
#include "Miner.h"

int main (int argc, char* const argv[]){
	if(argc == 1 || argc == 2 && (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0)){
		std::cerr << "Usage: smine [options] FILE" << std::endl;
		std::cerr << "Search for correlated occurrences within sequences" << std::endl;
		std::cerr << "FILE is a binary file containing examples (see data)" << std::endl << std::endl;
		std::cerr << "Options:"<< std::endl;
		std::cerr << "  -ml INT: maximum number f levels to be mined within sequences" << std::endl;
		std::cerr << "  -ms INT: minimum support for patterns" << std::endl;
		std::cerr << "  -omc ITEMTYPE FLOAT: oriented mining confidence, mine for minimum confidence (%) of item and childrens" << std::endl;
		std::cerr << "  -omi FLOAT: inter target minimum confidence  (%) for oriented mining" << std::endl;
		std::cerr << "  -hierarchy FILE: hierarchy file, inheritance of categories" << std::endl;
		std::cerr << "  -translation FILE: translation file, correspondance between sequence items and tokens" << std::endl;
		std::cerr << "  -smooth FLOAT: smoothing factor for proba and confidence" << std::endl;
		std::cerr << "  -red FLOAT: reduction factor (%) for pattern clustering" << std::endl;
		std::cerr << "  -stats: outputs pattern and rule counts" << std::endl;
		std::cerr << "  -min: outputs minimal patterns (default is maximal patterns)" << std::endl;
		std::cerr << "  -segs: only consider structure patterns (no redundancy of contiguous items)" << std::endl;
		std::cerr << "  -st: only extract patterns that have on single target item" << std::endl;
		std::cerr << "  -lt: only extract patterns that have limited target item (no sequences of target)" << std::endl;
		std::cerr << "  -ot: also extract patterns that only targets" << std::endl;
		std::cerr << "  -h, --help: display this help" << std::endl;
		return 0;
	}
	Dataset* dataset = new Dataset(argv[argc - 1]);
	Miner* miner = new Miner();
	bool minimals = false, statistics = false, segmentals = false, singleTarget = false, limitedTarget = false, onlyTarget = false;
	int maximumLevel = 0, minimumSupport = 0;
	double minimumConfidence = 0, minimumConfidenceInter = 0, smoothing = 0, reductionFactor = 0;
	ITEMTYPE rootTarget = 0;
	char *translationFile = NULL, *hierarchyFile = NULL;
	for(int i = 1; i < argc - 1; i++){
		if(strcmp(argv[i], "-ml") == 0 && i != argc - 2)
			maximumLevel = atoi(argv[++i]);
		else if(strcmp(argv[i], "-mf") == 0 && i != argc - 2)
			minimumSupport = atoi(argv[++i]);
		else if(strcmp(argv[i], "-omc") == 0 && i != argc - 3){
			rootTarget = (ITEMTYPE)atoi(argv[++i]);
			minimumConfidence = (double)atof(argv[++i])/100;
		}
		else if(strcmp(argv[i], "-omi") == 0 && i != argc - 2)
			minimumConfidenceInter = (double)atof(argv[++i])/100;
		else if(strcmp(argv[i], "-hierarchy") == 0 && i != argc - 2)
			hierarchyFile = argv[++i];
		else if(strcmp(argv[i], "-translation") == 0 && i != argc - 2)
			translationFile = argv[++i];
		else if(strcmp(argv[i], "-smooth") == 0 && i != argc - 2)
			smoothing = (double)atof(argv[++i]);
		else if(strcmp(argv[i], "-red") == 0 && i != argc - 2)
			reductionFactor = (double)atof(argv[++i])/100;
		else if(strcmp(argv[i], "-stats") == 0)
			statistics = true;
		else if(strcmp(argv[i], "-min") == 0)
			minimals = true;
		else if(strcmp(argv[i], "-segs") == 0)
			segmentals = true;
		else if(strcmp(argv[i], "-st") == 0)
			singleTarget = true;
		else if(strcmp(argv[i], "-lt") == 0)
			limitedTarget = true;
		else if(strcmp(argv[i], "-ot") == 0)
			onlyTarget = true;
		else{
			std::cerr << "Unknown option \"" << argv[i] << "\" (-h for help)" << std::endl;
			return 1;
		}
	}
	if(rootTarget)
		dataset->setRootTarget(rootTarget);
	if(hierarchyFile)
		dataset->setHierarchy(hierarchyFile);
	if(rootTarget)
		dataset->setTransactionsTarget();
	if(translationFile)
		dataset->setTranslation(translationFile);
	miner->run(dataset, maximumLevel, minimumSupport, minimumConfidence, minimumConfidenceInter, smoothing, reductionFactor, statistics, minimals, segmentals, singleTarget, limitedTarget, onlyTarget);
	delete miner;
	delete dataset;
	return 0;
}


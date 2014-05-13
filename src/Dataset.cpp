#include <fstream>
#include <cstring>
#include <iostream>
#include <stdlib.h>
#include "global.h"
#include "Dataset.h"

Dataset::Dataset(char* name){
	m_transactions = NULL;
	m_maximumItemType = 0;
	m_nbItems = 0;
	m_translation = NULL;
	m_hierarchy = NULL;
	setTransactions(name);
}

Dataset::~Dataset(){
	if(m_transactions){
		Transaction* currentTransaction = m_transactions;
		while(currentTransaction){
			Item* currentItem = currentTransaction->m_items;
			while(currentItem){
				Item* currentItemNext = currentItem->m_next;
				delete currentItem;
				currentItem = currentItemNext;
			}
			Transaction* currentTransactionNext = currentTransaction->m_next;
			delete currentTransaction;
			currentTransaction = currentTransactionNext;
		}
	}
	if(m_hierarchy){
		for(ITEMTYPE i = 0; i < m_maximumItemType + 1; i++)
			if(m_hierarchy[i]){
				ItemTypeList* currentItem = m_hierarchy[i];
				while(currentItem){
					ItemTypeList* currentItemNext = currentItem->m_next;
					delete currentItem;
					currentItem = currentItemNext;
				}
			}
		delete m_hierarchy;
	}
	if(m_translation){
		for(ITEMTYPE i = 0; i < m_maximumItemType + 1; i++)
			if(m_translation[i])
				delete m_translation[i];
		delete m_translation;
	}
}

void Dataset::setTransactions(char* name){
	char* buffer = new char [MAX_TRANSACTION];
	Transaction* currentTransaction = NULL;
	std::ifstream input(name);
	while(!input.eof()){
		input.getline(buffer, MAX_TRANSACTION, '\n');
		if((strlen(buffer) > 0) && (buffer[0] != '#')){
			Transaction* transaction = readTransactionLine(buffer);
			m_nbItems += transaction->m_nbItems;
			if(currentTransaction){
				currentTransaction->m_next = transaction;
				currentTransaction = currentTransaction->m_next;
			}
			else {
				currentTransaction = transaction;
				m_transactions = currentTransaction;
			}
		}
	}
	input.close();
}

Transaction* Dataset::readTransactionLine(char* buffer){
	Transaction* transaction = new Transaction;
	transaction->m_next = NULL;
	transaction->m_items = NULL;
	transaction->m_nbItems = 0;
	Item* currentItem = NULL;
	Item* nextItem = NULL;
	bool disjunction = false;
	bool disjunctionEnd = false;
	Item* disjunctionFirstItem = NULL;
	unsigned long i = 0, j = 0;
	bool done = false;
	while(!done){
		if(buffer[i] == '\0' || buffer[i] == '\n')
			done = true;
		if(buffer[i] == '+' || buffer[i] == ' ' || buffer[i] == '\0' || buffer[i] == '\n'){
			if(disjunction && !disjunctionFirstItem)
				disjunctionFirstItem = currentItem;
			if(buffer[i] == '+')
				disjunction = true;
			else if(disjunction)
				disjunction = false;
			buffer[i] = '\0';
			ITEMTYPE tmp = (ITEMTYPE)atoi(&buffer[j]);
			if(tmp > m_maximumItemType)
				m_maximumItemType = tmp;
			if(tmp > 0){
				nextItem = new Item;
				nextItem->m_itemType = tmp;
				nextItem->m_next = NULL;
				nextItem->m_previous = NULL;
				nextItem->m_alt = NULL;
				if(!disjunction)
					transaction->m_nbItems++;
				if(currentItem){
					if(disjunctionEnd){
						while(disjunctionFirstItem){
							disjunctionFirstItem->m_next = nextItem;
							disjunctionFirstItem = disjunctionFirstItem->m_alt;
						}
						disjunctionEnd = false;
					}else if(disjunctionFirstItem){
						currentItem->m_alt = nextItem;
						if(!disjunction)
							disjunctionEnd = true;
					}else
						currentItem->m_next = nextItem;
				}else
					transaction->m_items = nextItem;
				currentItem = nextItem;
			}
			j = i + 1;
		}
		i++;
	}
	currentItem = NULL;
	nextItem = transaction->m_items;
	while(nextItem){
		Item* nextItemAlt = nextItem;
		while(nextItemAlt){
			nextItemAlt->m_previous = currentItem;
			nextItemAlt = nextItemAlt->m_alt;
		}
		currentItem = nextItem;
		nextItem = nextItem->m_next;
	}
	return transaction;
}

Transaction* Dataset::getTransactions(){
	return m_transactions;
}

ITEMTYPE Dataset::getMaximumItemType(){
	return m_maximumItemType;
}

int Dataset::getNbItems(){
	return m_nbItems;
}

void Dataset::setRootTarget(ITEMTYPE rootTarget){
	m_rootTarget = rootTarget;
}

ITEMTYPE Dataset::getRootTarget(){
	return m_rootTarget;
}


void Dataset::setHierarchy(char* name){
	m_hierarchy = new ItemTypeList*[m_maximumItemType + 1];
	char buffer[MAX_TRANSACTION];
	std::ifstream input(name);
	for(int i = 0; i < m_maximumItemType + 1; i++)
		m_hierarchy[i] = NULL;
	while(!input.eof()){
		input.getline(buffer, MAX_TRANSACTION, '\n');
		if(buffer[0] != '#'){
			if(strlen(buffer) > 0){
				ItemTypeList* hierarchy = readHierarchyLine(buffer);
				ItemTypeList* hierarchyLast = hierarchy;
				while(hierarchyLast && hierarchyLast->m_next)
					hierarchyLast = hierarchyLast->m_next;
				if(hierarchyLast && hierarchyLast->m_itemType)
					m_hierarchy[hierarchyLast->m_itemType] = hierarchy;
			}
		}
	}
	input.close();
}

ItemTypeList** Dataset::getHierarchy(){
	return m_hierarchy;
}

ItemTypeList* Dataset::readHierarchyLine(char* buffer){
	ItemTypeList* firstItem = NULL, * currentItem = NULL, * nextItem = NULL;
	unsigned long i = 0, j = 0;
	bool done = false;
	bool isTarget = false;
	while(!done){
		if(buffer[i] == '\0' || buffer[i] == '\n')
			done = true;
		if(buffer[i] == ' ' || buffer[i] == '\0' || buffer[i] == '\n'){
			buffer[i] = '\0';
			ITEMTYPE tmp = (ITEMTYPE)atoi(&buffer[j]);
			if(tmp > m_maximumItemType)
				m_maximumItemType = tmp;
			if(tmp > 0){
				if(tmp == m_rootTarget)
					isTarget = true;
				nextItem = new ItemTypeList;
				nextItem->m_itemType = tmp;
				nextItem->m_isTarget = isTarget;
				nextItem->m_next = NULL;
				if(currentItem)
					currentItem->m_next = nextItem;
				else
					firstItem = nextItem;
				currentItem = nextItem;
			}
			j = i + 1;
		}
		i++;
	}
	return firstItem;
}

void Dataset::setTransactionsTarget(){
	Transaction* currentTransaction = m_transactions;
	while(currentTransaction){
		Item* currentItem = currentTransaction->m_items;
		while(currentItem){
			Item* currentItemAlt = currentItem;
			while(currentItemAlt){
				ItemTypeList* currentItemAltHierarchy = m_hierarchy[currentItemAlt->m_itemType];
				while(!currentItemAltHierarchy->m_isTarget && currentItemAltHierarchy->m_next)
					currentItemAltHierarchy = currentItemAltHierarchy->m_next;
				if(currentItemAltHierarchy->m_isTarget)
					currentItemAlt->m_isTarget = true;
				currentItemAlt = currentItemAlt->m_alt;
			}
			currentItem = currentItem->m_next;
		}
		currentTransaction = currentTransaction->m_next;
	}
}

void Dataset::setTranslation(char* name){
	m_translation = new char*[m_maximumItemType + 2];
	for(ITEMTYPE i = 0; i < m_maximumItemType + 2; i++)
		m_translation[i] = NULL;
	char buffer[MAX_TRANSACTION];
	std::ifstream input(name);
	ITEMTYPE i = 1;
	while((!input.eof())&&(i <= m_maximumItemType)){
		input.getline(buffer, MAX_TRANSACTION, '\n');
		int j = 0;
		while(buffer[j] != ' ')
			j++;
		j++;
		m_translation[atoi(buffer)] = new char[strlen(&buffer[j])+1];
		strcpy(m_translation[atoi(buffer)], &buffer[j]);
	}
	input.close();
}

char** Dataset::getTranslation(){
	return m_translation;
}


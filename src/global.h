#ifndef _GLOBAL_H
#define _GLOBAL_H

#define ITEMTYPE unsigned int
#define MAX_TRANSACTION 1000000
#define MAX_LEVEL 500

struct ItemTypeList {
	ITEMTYPE m_itemType;
	bool m_isTarget;
	ItemTypeList* m_next;
};

struct Item {
	ITEMTYPE m_itemType;
	bool m_isTarget;
	Item* m_next;
	Item* m_previous;
	Item* m_alt;
};

struct Transaction {
	Item* m_items;
	Transaction* m_next;
	int m_nbItems;
};

#endif


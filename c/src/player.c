#include <stdlib.h>
#include "player.h"



//Position and Room State

int player_get_room(const Player *p) {
    if (p == NULL) {
        return -1;
    }
    return p->room_id;
}

Status player_get_position(const Player *p, int *x_out, int *y_out) {
    if (p == NULL || x_out == NULL || y_out == NULL) {
        return INVALID_ARGUMENT;
    }
    *x_out = p->x;
    *y_out = p->y;
    return OK;
}

Status player_set_position(Player *p, int x, int y) {
    if (p == NULL) {
        return INVALID_ARGUMENT;
    }
    p->x = x;
    p->y = y;
    return OK;
}

Status player_move_to_room(Player *p, int new_room_id) {
    if (p == NULL) {
        return INVALID_ARGUMENT;
    }
    p->room_id = new_room_id;
    return OK;
}

//new implamentations and updates

//Lifecycle
// Update player_create:
Status player_create(int initial_room_id, int initial_x, int initial_y, Player **player_out) {
    if (player_out == NULL) {
        return INVALID_ARGUMENT;
    }

    Player *p = malloc(sizeof(Player));
    if (p == NULL) {
        return NO_MEMORY;
    }

    p->room_id = initial_room_id;
    p->x = initial_x;
    p->y = initial_y;
    
    // NEW FOR A2:
    p->collected_treasures = NULL;
    p->collected_count = 0;

    *player_out = p;
    return OK;
}

// Update player_destroy:
void player_destroy(Player *p) {
    if (p == NULL) {
        return;
    }
    
    // NEW FOR A2: Free the array (but NOT the treasures themselves - rooms own them)
    free(p->collected_treasures);
    
    free(p);
}

// Update player_reset_to_start:
Status player_reset_to_start(Player *p, int starting_room_id, int start_x, int start_y) {
    if (p == NULL) {
        return INVALID_ARGUMENT;
    }

    p->room_id = starting_room_id;
    p->x = start_x;
    p->y = start_y;
    
    // NEW FOR A2: Clear collected treasures
    free(p->collected_treasures);
    p->collected_treasures = NULL;
    p->collected_count = 0;

    return OK;
}

//Reset

Status player_try_collect(Player *p, Treasure *treasure) {
    if (!p || !treasure) {
        return NULL_POINTER;
    }
    
    // Check if already collected
    if (treasure->collected) {
        return INVALID_ARGUMENT;
    }
    
    // Check if already in player's array
    for (int i = 0; i < p->collected_count; i++) {
        if (p->collected_treasures[i]->id == treasure->id) {
            return INVALID_ARGUMENT;
        }
    }
    
    // Expand array
    Treasure **new_array = realloc(p->collected_treasures, 
                                   sizeof(Treasure*) * (p->collected_count + 1));
    if (!new_array) {
        return NO_MEMORY;
    }
    
    p->collected_treasures = new_array;
    p->collected_treasures[p->collected_count] = treasure;  // Borrow pointer
    p->collected_count++;
    
    treasure->collected = true;  // Mark as collected
    
    return OK;
}

bool player_has_collected_treasure(const Player *p, int treasure_id) {
    if (!p || treasure_id < 0) {
        return false;
    }
    
    for (int i = 0; i < p->collected_count; i++) {
        if (p->collected_treasures[i]->id == treasure_id) {
            return true;
        }
    }
    return false;
}

int player_get_collected_count(const Player *p) {
    if (!p) {
        return 0;
    }
    return p->collected_count;
}

const Treasure * const * player_get_collected_treasures(const Player *p, int *count_out) {
    if (!p || !count_out) {
        return NULL;
    }
    
    *count_out = p->collected_count;
    return (const Treasure * const *)p->collected_treasures;
}
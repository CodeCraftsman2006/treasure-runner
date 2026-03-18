#include "room.h"
#include <stdlib.h>
#include <string.h>

// Convert 2D coordinates to 1D index in the floor grid
static int index_1d(const Room *r, int x, int y) {
    return y * r->width + x;
}

// Check if a position is inside the room bounds
static bool in_bounds(const Room *r, int x, int y) {
    return x >= 0 && y >= 0 && x < r->width && y < r->height;
}


// Get the width of the room
int room_get_width(const Room *r) {
    return r ? r->width : 0;
}

// Get the height of the room
int room_get_height(const Room *r) {
    return r ? r->height : 0;
}

// Set or replace the floor grid for the room
Status room_set_floor_grid(Room *r, bool *floor_grid) {
    if (!r){
        return INVALID_ARGUMENT;
    }
    free(r->floor_grid);
    r->floor_grid = floor_grid;
    return OK;
}

// Set or replace the portals for the room
Status room_set_portals(Room *r, Portal *portals, int portal_count) {
    if (!r || (portal_count > 0 && !portals)){
         return INVALID_ARGUMENT;
    }
    // Free previous portal names and array
    for (int i = 0; i < r->portal_count; i++) {
        free(r->portals[i].name);
    }
    free(r->portals);

    // Take ownership of new portal array
    r->portals = portals;
    r->portal_count = portal_count;

    return OK;
}

// Set or replace treasures for the room
Status room_set_treasures(Room *r, Treasure *treasures, int treasure_count) {
    if (!r || (treasure_count > 0 && !treasures)) {return INVALID_ARGUMENT;}

    // Free old treasure names and array
    for (int i = 0; i < r->treasure_count; i++) {
        free(r->treasures[i].name);
    }
    free(r->treasures);

    r->treasures = treasures;
    r->treasure_count = treasure_count;

    return OK;
}

// Add a new treasure into the room
Status room_place_treasure(Room *r, const Treasure *treasure) {
    if (!r || !treasure) {return INVALID_ARGUMENT;}

    Treasure *new_array = realloc(r->treasures, sizeof(Treasure) * (r->treasure_count + 1));
    if (!new_array) {return NO_MEMORY;}

    r->treasures = new_array;

    // Copy the treasure into the new slot
    Treasure *t = &r->treasures[r->treasure_count];
    *t = *treasure;

    // Duplicate name if present
    if (treasure->name) {
        t->name = malloc(strlen(treasure->name) + 1);
        if (!t->name) return NO_MEMORY;
        strcpy(t->name, treasure->name);
    }

    r->treasure_count++;
    return OK;
}


// Get portal destination room ID at a specific position
int room_get_portal_destination(const Room *r, int x, int y) {
    if (!r) {return -1;}

    for (int i = 0; i < r->portal_count; i++) {
        if (r->portals[i].x == x && r->portals[i].y == y) {
            return r->portals[i].target_room_id;
        }
    }
    return -1;
}




// Find a starting position in the room
Status room_get_start_position(const Room *r, int *x_out, int *y_out) {
    if (!r || !x_out || !y_out) {
        return INVALID_ARGUMENT;
    }
    // Prefer the first portal
    if (r->portal_count > 0) {
        *x_out = r->portals[0].x;
        *y_out = r->portals[0].y;
        return OK;
    }

    // Otherwise find any walkable tile
    for (int y = 0; y < r->height; y++) {
        for (int x = 0; x < r->width; x++) {
            if (room_is_walkable(r, x, y)) {
                *x_out = x;
                *y_out = y;
                return OK;
            }
        }
    }

    return ROOM_NOT_FOUND;
}




int room_get_id(const Room *r) {
    if (!r) {
        return -1;
    }
    return r->id;
}




















//_________________________________________________________________________


//updated the old the function




// Update room_is_walkable - check for pushables:
bool room_is_walkable(const Room *r, int x, int y) {
    if (!r || !in_bounds(r, x, y)) {
        return false;
    }

    // Check floor grid
    if (!r->floor_grid) {
        if (x <= 0 || y <= 0 || x >= r->width - 1 || y >= r->height - 1) {
            return false;
        }
    } else {
        if (!r->floor_grid[index_1d(r, x, y)]) {
            return false;
        }
    }
    
    // NEW FOR A2: Check for pushables
    if (room_has_pushable_at(r, x, y, NULL)) {
        return false;
    }
    
    return true;
}

// Update room_get_treasure_at - check if collected:
int room_get_treasure_at(const Room *r, int x, int y) {
    if (!r) {
        return -1;
    }

    for (int i = 0; i < r->treasure_count; i++) {
        // NEW FOR A2: Only return if NOT collected
        if (r->treasures[i].x == x && r->treasures[i].y == y && 
            !r->treasures[i].collected) {
            return r->treasures[i].id;
        }
    }
    return -1;
}

// Update room_classify_tile - add pushable check:
RoomTileType room_classify_tile(const Room *r, int x, int y, int *out_id) {
    if (!r || !in_bounds(r, x, y)) {
        return ROOM_TILE_INVALID;
    }

    // NEW FOR A2: Check pushables first
    int pushable_idx = 0;
    if (room_has_pushable_at(r, x, y, &pushable_idx)) {
        if (out_id) {
            *out_id = pushable_idx;
        }
        return ROOM_TILE_PUSHABLE;
    }

    // Check treasure (only if NOT collected)
    int id = room_get_treasure_at(r, x, y);
    if (id != -1) {
        if (out_id) {
            *out_id = id;
        }
        return ROOM_TILE_TREASURE;
    }

    // Check portal
    id = room_get_portal_destination(r, x, y);
    if (id != -1) {
        if (out_id) {
            *out_id = id;
        }
        return ROOM_TILE_PORTAL;
    }

    if (room_is_walkable(r, x, y)) {
        return ROOM_TILE_FLOOR;
    }

    return ROOM_TILE_WALL;
}

// Update room_render - add pushables, skip collected treasures:
Status room_render(const Room *r, const Charset *charset, char *buffer, int buffer_width, int buffer_height) {
    if (!r || !charset || !buffer) {
        return INVALID_ARGUMENT;
    }
    if (buffer_width != r->width || buffer_height != r->height) {
        return INVALID_ARGUMENT;
    }

    // Base layer
    for (int row = 0; row < r->height; row++) {
        for (int col = 0; col < r->width; col++) {
            int i = row * r->width + col;
            if (room_is_walkable(r, col, row)) {
                buffer[i] = (char)charset->floor;
            } else {
                buffer[i] = (char)charset->wall;
            }
        }
    }

    // Overlay treasures (only if NOT collected)
    for (int i = 0; i < r->treasure_count; i++) {
        if (!r->treasures[i].collected) {  // NEW FOR A2
            int col = r->treasures[i].x;
            int row = r->treasures[i].y;
            buffer[row * r->width + col] = (char)charset->treasure;
        }
    }

    // Overlay portals
    for (int i = 0; i < r->portal_count; i++) {
        int col = r->portals[i].x;
        int row = r->portals[i].y;
        buffer[row * r->width + col] = (char)charset->portal;
    }
    
    // NEW FOR A2: Overlay pushables
    for (int i = 0; i < r->pushable_count; i++) {
        int col = r->pushables[i].x;
        int row = r->pushables[i].y;
        buffer[row * r->width + col] = (char)charset->pushable;
    }

    return OK;
}

// Update room_destroy - free new fields:
void room_destroy(Room *r) {
    if (!r) {
        return;
    }

    free(r->name);
    free(r->floor_grid);

    for (int i = 0; i < r->portal_count; i++) {
        free(r->portals[i].name);
    }
    free(r->portals);

    for (int i = 0; i < r->treasure_count; i++) {
        free(r->treasures[i].name);
    }
    free(r->treasures);
    
    // NEW FOR A2:
    for (int i = 0; i < r->pushable_count; i++) {
        free(r->pushables[i].name);
    }
    free(r->pushables);
    
    free(r->switches);
    free(r->neighbors);

    free(r);
}




// Update room_create - initialize new fields:
Room *room_create(int id, const char *name, int width, int height) {
    Room *r = malloc(sizeof(Room));
    if (!r) {
        return NULL;
    }

    if (width < 1) width = 1;
    if (height < 1) height = 1;
    
    r->id = id;
    r->width = width;
    r->height = height;

    if (name) {
        r->name = malloc(strlen(name) + 1);
        if (!r->name) {
            free(r);
            return NULL;
        }
        strcpy(r->name, name);
    } else {
        r->name = NULL;
    }

    r->floor_grid = NULL;
    r->portals = NULL;
    r->portal_count = 0;
    r->treasures = NULL;
    r->treasure_count = 0;
    
    // NEW FOR A2:
    r->pushables = NULL;
    r->pushable_count = 0;
    r->switches = NULL;
    r->switch_count = 0;
    r->neighbors = NULL;
    r->neighbor_count = 0;

    return r;
}




/*
new functions implamented
*/

Status room_pick_up_treasure(Room *r, int treasure_id, Treasure **treasure_out) {
    if (!r || !treasure_out) {
        return INVALID_ARGUMENT;
    }
    
    // Find treasure
    for (int i = 0; i < r->treasure_count; i++) {
        if (r->treasures[i].id == treasure_id) {
            if (r->treasures[i].collected) {
                return INVALID_ARGUMENT;  // Already collected
            }
            
            r->treasures[i].collected = true;
            *treasure_out = &r->treasures[i];  // Return pointer to room-owned treasure
            return OK;
        }
    }
    
    return ROOM_NOT_FOUND;
}

void destroy_treasure(Treasure *t) {
    if (!t) {
        return;
    }
    free(t->name);
    free(t);
}

bool room_has_pushable_at(const Room *r, int x, int y, int *pushable_idx_out) {
    if (!r) {
        return false;
    }
    
    for (int i = 0; i < r->pushable_count; i++) {
        if (r->pushables[i].x == x && r->pushables[i].y == y) {
            if (pushable_idx_out) {
                *pushable_idx_out = i;
            }
            return true;
        }
    }
    return false;
}

Status room_try_push(Room *r, int pushable_idx, Direction dir) {
    if (!r || pushable_idx < 0 || pushable_idx >= r->pushable_count) {
        return INVALID_ARGUMENT;
    }
    
    Pushable *p = &r->pushables[pushable_idx];
    int new_x = p->x;
    int new_y = p->y;
    
    // Calculate new position
    switch(dir) {
        case DIR_NORTH: new_y -= 1; break;
        case DIR_SOUTH: new_y += 1; break;
        case DIR_WEST:  new_x -= 1; break;
        case DIR_EAST:  new_x += 1; break;
        default: return INVALID_ARGUMENT;
    }
    
    // Check if new position is valid
    if (!room_is_walkable(r, new_x, new_y)) {
        return ROOM_IMPASSABLE;
    }
    
    // Check if another pushable is there
    if (room_has_pushable_at(r, new_x, new_y, NULL)) {
        return ROOM_IMPASSABLE;
    }
    
    // Move pushable
    p->x = new_x;
    p->y = new_y;
    
    return OK;
}
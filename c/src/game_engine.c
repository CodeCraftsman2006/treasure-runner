#include "game_engine.h"
#include "world_loader.h"
#include "room.h"
#include "player.h"
#include "graph.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* forward declarations for extended feature functions */
int room_get_total_treasure_count(const Room *r);
int room_get_uncollected_count(const Room *r);

//Internal helper to get the current room the player is in

static Room *get_player_room(const GameEngine *eng) {
    if (!eng || !eng->player || !eng->graph){ return NULL;}

    int room_id = player_get_room(eng->player);
    return (Room *)graph_get_payload(eng->graph, &room_id);
}

// Creation & Destruction
Status game_engine_create(const char *config_file_path, GameEngine **engine_out) {

    if (!config_file_path || !engine_out){
        return INVALID_ARGUMENT;
    }
    *engine_out = NULL;

    Graph *g = NULL;
    Room *first = NULL;
    int num_rooms = 0;
    Charset cs = {0};

    //here is where load world is called 
    Status s = loader_load_world(config_file_path, &g, &first, &num_rooms, &cs);

    // loader must succeed AND return a valid world
    if (s != OK || !g || !first || num_rooms <= 0) {
        if (g) graph_destroy(g);
        return WL_ERR_DATAGEN;  // or INTERNAL_ERROR
    }
    int start_x = 0;
    int start_y = 0;

    s = room_get_start_position(first, &start_x, &start_y);
    if (s != OK) {
        graph_destroy(g);
        return s;
    }

    Player *p = NULL;
    s = player_create(first->id, start_x, start_y, &p);
    if (s != OK) {
        graph_destroy(g);
        return s;
    }

    GameEngine *eng = malloc(sizeof(GameEngine));
    if (!eng) {
        player_destroy(p);
        graph_destroy(g);
        return NO_MEMORY;
    }

    eng->graph = g;
    eng->player = p;
    eng->charset = cs;
    eng->initial_room_id = first->id;
    eng->initial_player_x = start_x;
    eng->initial_player_y = start_y;
    eng->room_count = num_rooms;

    *engine_out = eng;
    return OK;
}

void game_engine_destroy(GameEngine *eng) {
    if (!eng) return;
    player_destroy(eng->player);
    graph_destroy(eng->graph);
    free(eng);
}

// Player Access

const Player *game_engine_get_player(const GameEngine *eng) {
    if (!eng) return NULL;
    return eng->player;
}

//Metadata
 
Status game_engine_get_room_count(const GameEngine *eng, int *count_out) {
    if (!eng){ return INVALID_ARGUMENT;}
    if (!count_out){ return NULL_POINTER;}

    *count_out = eng->room_count;
    return OK;
}

// Get current room dimensions
Status game_engine_get_room_dimensions(const GameEngine *eng,
                                       int *width_out,
                                       int *height_out)
{
    if (!eng){ return INVALID_ARGUMENT;}
    if (!width_out || !height_out) {return NULL_POINTER;}

    Room *r = get_player_room(eng);
    if (!r){return GE_NO_SUCH_ROOM;}

    *width_out = r->width;
    *height_out = r->height;
    return OK;
}

/// Rendering
Status game_engine_render_current_room(const GameEngine *eng, char **str_out) {
    if (!eng){ return INVALID_ARGUMENT;}
    if (!str_out){ return NULL_POINTER;}

    *str_out = NULL;

    Room *r = get_player_room(eng);
    if (!r) {return GE_NO_SUCH_ROOM;}

    int width = r->width;
    int height = r->height;

    // create flat buffer for room_render (no newlines)
    char *flat_buffer = malloc((size_t)width * (size_t)height);
    if (!flat_buffer) {return NO_MEMORY;}

    Status s = room_render(r, &eng->charset, flat_buffer, width, height);
    if (s != OK) {
        free(flat_buffer);
        return s;
    }

    //  overlay player
    int px = 0;
    int py = 0;
    s = player_get_position(eng->player, &px, &py);
    if (s != OK) {
        free(flat_buffer);
        return s;
    }

    if (px >= 0 && px < width && py >= 0 && py < height) {
        flat_buffer[py * width + px] = eng->charset.player;
    }

    // format into output string with newlines
    int output_size = (width + 1) * height + 1;  // +1 per row for \n, +1 for \0
    char *output = malloc(output_size);
    if (!output) {
        free(flat_buffer);
        return NO_MEMORY;
    }

    int out_idx = 0;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            output[out_idx++] = flat_buffer[y * width + x];
        }
        output[out_idx++] = '\n';  // add newline after each row
    }
    output[out_idx] = '\0';  // null terminate

    free(flat_buffer);
    *str_out = output;
    return OK;
}

/// room IDs

Status game_engine_get_room_ids(const GameEngine *eng, int **ids_out, int *count_out) {
    if (!eng){ return INVALID_ARGUMENT;}
    if (!ids_out || !count_out){ return NULL_POINTER;}

    const void * const *payloads = NULL;
    int count = 0;
    GraphStatus gs = graph_get_all_payloads(eng->graph, &payloads, &count);
    if (gs != GRAPH_STATUS_OK){ return INTERNAL_ERROR;}

    int *ids = malloc(sizeof(int) * count);
    if (!ids){ return NO_MEMORY;}

    for (int i = 0; i < count; i++) {
        ids[i] = ((Room *)payloads[i])->id;
    }

    *ids_out = ids;
    *count_out = count;
    return OK;
}


Status game_engine_render_room(const GameEngine *eng,
                               int room_id,
                               char **str_out)
{
    if (!eng) {return INVALID_ARGUMENT;}
    if (!str_out) {return NULL_POINTER;}

    *str_out = NULL;

    const void *payload = graph_get_payload(eng->graph, &room_id);
    Room *r = (Room *)payload;
    if (!r) return GE_NO_SUCH_ROOM;

    int width = r->width;
    int height = r->height;

    // create flat buffer
    char *flat_buffer = malloc((size_t)width * (size_t)height);
    if (!flat_buffer) return NO_MEMORY;

    Status s = room_render(r, &eng->charset, flat_buffer, width, height);
    if (s != OK) {
        free(flat_buffer);
        return s;
    }

    // format with newlines
    int output_size = (width + 1) * height + 1;
    char *output = malloc(output_size);
    if (!output) {
        free(flat_buffer);
        return NO_MEMORY;
    }

    int out_idx = 0;
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            output[out_idx++] = flat_buffer[y * width + x];
        }
        output[out_idx++] = '\n';
    }
    output[out_idx] = '\0';

    free(flat_buffer);
    *str_out = output;
    return OK;
}
//_________________________________________________________________________________

/* new functions and updates*/

// Add new function:
void game_engine_free_string(void *ptr) {
    free(ptr);
}

// Update game_engine_move_player - handle treasures and pushables:
Status game_engine_move_player(GameEngine *eng, Direction dir) {
    if (!eng || !eng->player) {
        return INVALID_ARGUMENT;
    }

    Room *current = get_player_room(eng);
    if (!current) {
        return INTERNAL_ERROR;
    }

    int x = 0;
    int y = 0;
    Status s = player_get_position(eng->player, &x, &y);
    if (s != OK) {
        return s;
    }

    // Calculate new position
    int new_x = x;
    int new_y = y;
    switch(dir) {
        case DIR_NORTH: new_y -= 1; break;
        case DIR_SOUTH: new_y += 1; break;
        case DIR_WEST:  new_x -= 1; break;
        case DIR_EAST:  new_x += 1; break;
        default: return INVALID_ARGUMENT;
    }

    // Bounds check
    if (new_x < 0 || new_x >= current->width ||
        new_y < 0 || new_y >= current->height) {
        return ROOM_IMPASSABLE;
    }

    // NEW FOR A2: Classify tile
    int tile_id = 0;
    RoomTileType tile = room_classify_tile(current, new_x, new_y, &tile_id);

    switch (tile) {
        case ROOM_TILE_WALL:
            return ROOM_IMPASSABLE;
            
        case ROOM_TILE_PUSHABLE:
            // Try to push
            s = room_try_push(current, tile_id, dir);
            if (s != OK) {
                return s;  // Push failed
            }
            // Push succeeded, move player
            break;
            
        case ROOM_TILE_TREASURE:
            // Collect treasure
            {
                Treasure *treasure = NULL;
                s = room_pick_up_treasure(current, tile_id, &treasure);
                if (s == OK && treasure) {
                    player_try_collect(eng->player, treasure);
                }
            }
            break;
            
        case ROOM_TILE_PORTAL:
            {
                int target_id = room_get_portal_destination(current, new_x, new_y);
                if (target_id < 0) {
                    return ROOM_IMPASSABLE;
                }
                Room *target = (Room *)graph_get_payload(eng->graph, &target_id);
                if (!target) {
                    return GE_NO_SUCH_ROOM;
                }
                int entry_x = 0;
                int entry_y = 0;
                s = room_get_start_position(target, &entry_x, &entry_y);
                if (s != OK) {
                    return s;
                }
                s = player_move_to_room(eng->player, target_id);
                if (s != OK) {
                    return s;
                }
                return player_set_position(eng->player, entry_x, entry_y);
            }
            
        case ROOM_TILE_FLOOR:
        case ROOM_TILE_INVALID:
        default:
            break;
    }

    return player_set_position(eng->player, new_x, new_y);
}

// Update game_engine_reset - reset pushables and treasures:
Status game_engine_reset(GameEngine *eng) {
    if (!eng || !eng->player) {
        return INVALID_ARGUMENT;
    }

    // Reset player
    Status s = player_reset_to_start(eng->player,
                                     eng->initial_room_id,
                                     eng->initial_player_x,
                                     eng->initial_player_y);
    if (s != OK) {
        return s;
    }

    // NEW FOR A2: Reset all rooms' pushables and treasures
    const void * const *payloads = NULL;
    int count = 0;
    if (graph_get_all_payloads(eng->graph, &payloads, &count) == GRAPH_STATUS_OK) {
        for (int i = 0; i < count; i++) {
            Room *r = (Room *)payloads[i];
            
            // Reset pushables to initial positions
            for (int j = 0; j < r->pushable_count; j++) {
                r->pushables[j].x = r->pushables[j].initial_x;
                r->pushables[j].y = r->pushables[j].initial_y;
            }
            
            // Reset treasures
            for (int j = 0; j < r->treasure_count; j++) {
                r->treasures[j].x = r->treasures[j].initial_x;
                r->treasures[j].y = r->treasures[j].initial_y;
                r->treasures[j].collected = false;
            }
        }
    }

    return OK;
}

/* ── EXTENDED: COLLECT ALL TREASURE ─────────────────────── */

/* Total treasure count across ALL rooms */
Status game_engine_get_total_treasure_count(const GameEngine *eng, int *count_out) {
    if (!eng) { return INVALID_ARGUMENT; }
    if (!count_out) { return NULL_POINTER; }

    const void * const *payloads = NULL;
    int room_count = 0;
    if (graph_get_all_payloads(eng->graph, &payloads, &room_count) != GRAPH_STATUS_OK) {
        return INTERNAL_ERROR;
    }

    int total = 0;
    for (int i = 0; i < room_count; i++) {
        total += room_get_total_treasure_count((Room *)payloads[i]);
    }
    *count_out = total;
    return OK;
}

/* Returns 1 if the player has collected every treasure in the world, 0 otherwise */
Status game_engine_is_victory(const GameEngine *eng, int *result_out) {
    if (!eng) { return INVALID_ARGUMENT; }
    if (!result_out) { return NULL_POINTER; }

    const void * const *payloads = NULL;
    int room_count = 0;
    if (graph_get_all_payloads(eng->graph, &payloads, &room_count) != GRAPH_STATUS_OK) {
        return INTERNAL_ERROR;
    }

    for (int i = 0; i < room_count; i++) {
        if (room_get_uncollected_count((Room *)payloads[i]) > 0) {
            *result_out = 0;
            return OK;
        }
    }
    *result_out = 1;
    return OK;
}

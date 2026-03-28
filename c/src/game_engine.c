#include "game_engine.h"
#include "world_loader.h"
#include "room.h"
#include "player.h"
#include "graph.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

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

static Status calc_new_pos(Direction dir, int cx, int cy, int *nx, int *ny) {
    *nx = cx;
    *ny = cy;
    if (dir == DIR_NORTH) {
        *ny = cy - 1;
    } else if (dir == DIR_WEST) {
        *nx = cx - 1;
    } else if (dir == DIR_SOUTH) {
        *ny = cy + 1;
    } else if (dir == DIR_EAST) {
        *nx = cx + 1;
    } else {
        return INVALID_ARGUMENT;
    }
    return OK;
}

static Status handle_pushable(Room *r, int new_x, int new_y, Direction dir,
                               int pushable_idx) {
    int push_x = new_x;
    int push_y = new_y;
    if (dir == DIR_NORTH) {
        push_y--;
    } else if (dir == DIR_WEST) {
        push_x--;
    } else if (dir == DIR_SOUTH) {
        push_y++;
    } else if (dir == DIR_EAST) {
        push_x++;
    }
    if (room_get_treasure_at(r, push_x, push_y) != -1) {
        return ROOM_IMPASSABLE;
    }
    if (room_get_portal_destination(r, push_x, push_y) != -1) {
        return ROOM_IMPASSABLE;
    }
    if (room_try_push(r, pushable_idx, dir) != OK) {
        return ROOM_IMPASSABLE;
    }
    return OK;
}

static Status handle_portal(GameEngine *eng, Room *r, int new_x, int new_y) {
    int dest = room_get_portal_destination(r, new_x, new_y);
    if (dest == -1) {
        return OK;
    }
    Room key;
    key.id = dest;
    Room *target_r = (Room *)graph_get_payload(eng->graph, &key);
    if (target_r == NULL) {
        return GE_NO_SUCH_ROOM;
    }
    if (player_move_to_room(eng->player, dest) != OK) {
        return INTERNAL_ERROR;
    }
    int target_x = 0;
    int target_y = 0;
    if (room_get_start_position(target_r, &target_x, &target_y) != OK) {
        return INTERNAL_ERROR;
    }
    if (player_set_position(eng->player, target_x, target_y) != OK) {
        return INTERNAL_ERROR;
    }
    int tid = room_get_treasure_at(target_r, target_x, target_y);
    if (tid != -1) {
        Treasure *t = NULL;
        if (room_pick_up_treasure(target_r, tid, &t) == OK && t != NULL) {
            t->collected = false;
            player_try_collect(eng->player, t);
        }
    }
    return OK;
}

Status game_engine_move_player(GameEngine *eng, Direction dir) {
    if (eng == NULL || eng->player == NULL) {
        return INVALID_ARGUMENT;
    }
    Room *r = get_player_room(eng);
    if (r == NULL) {
        return INTERNAL_ERROR;
    }
    int cx = 0;
    int cy = 0;
    if (player_get_position(eng->player, &cx, &cy) != OK) {
        return INTERNAL_ERROR;
    }
    int new_x = 0;
    int new_y = 0;
    if (calc_new_pos(dir, cx, cy, &new_x, &new_y) != OK) {
        return INVALID_ARGUMENT;
    }

    int treasure_id = room_get_treasure_at(r, new_x, new_y);
    if (treasure_id != -1) {
        Treasure *t = NULL;
        if (room_pick_up_treasure(r, treasure_id, &t) == OK && t != NULL) {
            t->collected = false;
            player_try_collect(eng->player, t);
        }
        return OK;
    }

    int pushable_idx = -1;
    if (room_has_pushable_at(r, new_x, new_y, &pushable_idx)) {
        Status ps = handle_pushable(r, new_x, new_y, dir, pushable_idx);
        if (ps != OK) {
            return ps;
        }
    }

    if (!room_is_walkable(r, new_x, new_y)) {
        return ROOM_IMPASSABLE;
    }

    /*
    int dest = room_get_portal_destination(r, new_x, new_y);
    if (dest != -1) {
        return handle_portal(eng, r, new_x, new_y);
    }
    */

    return player_set_position(eng->player, new_x, new_y);
}

Status game_engine_reset(GameEngine *eng) {
    if (!eng || !eng->player) {
        return INVALID_ARGUMENT;
    }

    Status s = player_reset_to_start(eng->player,
                                     eng->initial_room_id,
                                     eng->initial_player_x,
                                     eng->initial_player_y);
    if (s != OK) {
        return s;
    }

    const void * const *payloads = NULL;
    int count = 0;
    if (graph_get_all_payloads(eng->graph, &payloads, &count) == GRAPH_STATUS_OK) {
        for (int i = 0; i < count; i++) {
            Room *r = (Room *)payloads[i];
            for (int j = 0; j < r->pushable_count; j++) {
                r->pushables[j].x = r->pushables[j].initial_x;
                r->pushables[j].y = r->pushables[j].initial_y;
            }
            for (int j = 0; j < r->treasure_count; j++) {
                r->treasures[j].x = r->treasures[j].initial_x;
                r->treasures[j].y = r->treasures[j].initial_y;
                r->treasures[j].collected = false;
            }
        }
    }
    return OK;
}

// Python-friendly wrapper: move through a portal if on one
Status game_engine_try_portal(GameEngine *eng) {
    if (!eng || !eng->player) return INVALID_ARGUMENT;

    Room *r = get_player_room(eng);
    if (!r) return INTERNAL_ERROR;

    int cx = 0, cy = 0;
    if (player_get_position(eng->player, &cx, &cy) != OK) return INTERNAL_ERROR;

    return handle_portal(eng, r, cx, cy);
}
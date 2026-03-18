#include "world_loader.h"
#include "room.h"
#include "graph.h"
#include "datagen.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static int compare_rooms(const void *a, const void *b)
{
    const Room *ra = a;
    const Room *rb = b;

    if (!ra || !rb) return 0;

    return ra->id - rb->id;
}

static Status copy_floor_grid(Room *r, const DG_Room *dg)
{
    if (!dg->floor_grid) {
        return OK;
    }
    size_t count = (size_t)dg->width * (size_t)dg->height;
    bool *grid_copy = malloc(sizeof(bool) * count);
    if (!grid_copy) {
        return NO_MEMORY;
    }
    memcpy(grid_copy, dg->floor_grid, sizeof(bool) * count);
    if (room_set_floor_grid(r, grid_copy) != OK) {
        free(grid_copy);
        return INTERNAL_ERROR;
    }
    return OK;
}

static Status copy_portals(Room *r, const DG_Room *dg)
{
    if (dg->portal_count <= 0 || !dg->portals) {
        return OK;
    }
    Portal *copy = malloc(sizeof(Portal) * dg->portal_count);
    if (!copy) {
        return NO_MEMORY;
    }
    for (int i = 0; i < dg->portal_count; i++) {
        copy[i].id = dg->portals[i].id;
        copy[i].x = dg->portals[i].x;
        copy[i].y = dg->portals[i].y;
        copy[i].target_room_id = dg->portals[i].neighbor_id;
        copy[i].name = NULL;
    }
    if (room_set_portals(r, copy, dg->portal_count) != OK) {
        free(copy);
        return INTERNAL_ERROR;
    }
    return OK;
}

static Status copy_treasures(Room *r, const DG_Room *dg)
{
    if (dg->treasure_count <= 0 || !dg->treasures) {
        return OK;
    }
    Treasure *copy = malloc(sizeof(Treasure) * dg->treasure_count);
    if (!copy) {
        return NO_MEMORY;
    }
    for (int i = 0; i < dg->treasure_count; i++) {
        copy[i].id = dg->treasures[i].global_id;
        copy[i].x = dg->treasures[i].x;
        copy[i].y = dg->treasures[i].y;
        copy[i].initial_x = dg->treasures[i].x;
        copy[i].initial_y = dg->treasures[i].y;
        copy[i].starting_room_id = dg->id;
        copy[i].collected = false;
        copy[i].name = dg->treasures[i].name ? strdup(dg->treasures[i].name) : NULL;
        if (dg->treasures[i].name && !copy[i].name) {
            for (int j = 0; j < i; j++) {
                free(copy[j].name);
            }
            free(copy);
            return NO_MEMORY;
        }
    }
    if (room_set_treasures(r, copy, dg->treasure_count) != OK) {
        for (int i = 0; i < dg->treasure_count; i++) {
            free(copy[i].name);
        }
        free(copy);
        return INTERNAL_ERROR;
    }
    return OK;
}

static Status copy_pushables(Room *r, const DG_Room *dg)
{
    if (dg->pushable_count <= 0 || !dg->pushables) {
        return OK;
    }
    Pushable *copy = malloc(sizeof(Pushable) * dg->pushable_count);
    if (!copy) {
        return NO_MEMORY;
    }
    for (int i = 0; i < dg->pushable_count; i++) {
        copy[i].id = dg->pushables[i].id;
        copy[i].x = dg->pushables[i].x;
        copy[i].y = dg->pushables[i].y;
        copy[i].initial_x = dg->pushables[i].x;
        copy[i].initial_y = dg->pushables[i].y;
        copy[i].name = dg->pushables[i].name ? strdup(dg->pushables[i].name) : NULL;
        if (dg->pushables[i].name && !copy[i].name) {
            for (int j = 0; j < i; j++) {
                free(copy[j].name);
            }
            free(copy);
            return NO_MEMORY;
        }
    }
    r->pushables = copy;
    r->pushable_count = dg->pushable_count;
    return OK;
}

static Status copy_switches(Room *r, const DG_Room *dg)
{
    if (dg->switch_count <= 0 || !dg->switches) {
        return OK;
    }
    Switch *copy = malloc(sizeof(Switch) * dg->switch_count);
    if (!copy) {
        return NO_MEMORY;
    }
    for (int i = 0; i < dg->switch_count; i++) {
        copy[i].id = dg->switches[i].id;
        copy[i].x = dg->switches[i].x;
        copy[i].y = dg->switches[i].y;
        copy[i].portal_id = dg->switches[i].portal_id;
    }
    r->switches = copy;
    r->switch_count = dg->switch_count;
    return OK;
}

static Room *copy_room_from_datagen(const DG_Room *dg)
{
    if (!dg) {
        return NULL;
    }

    char temp_name[32];
    (void)snprintf(temp_name, sizeof(temp_name), "room_%d", dg->id);

    Room *r = room_create(dg->id, temp_name, dg->width, dg->height);
    if (!r) {
        return NULL;
    }

    if (copy_floor_grid(r, dg) != OK) {
        room_destroy(r);
        return NULL;
    }
    if (copy_portals(r, dg) != OK) {
        room_destroy(r);
        return NULL;
    }
    if (copy_treasures(r, dg) != OK) {
        room_destroy(r);
        return NULL;
    }
    if (copy_pushables(r, dg) != OK) {
        room_destroy(r);
        return NULL;
    }
    if (copy_switches(r, dg) != OK) {
        room_destroy(r);
        return NULL;
    }

    return r;
}

static Status load_rooms(Graph *g, Room ***room_array_out, int *count_out)
{
    int capacity = 8;
    Room **room_array = malloc(sizeof(Room *) * capacity);
    if (!room_array) {
        return NO_MEMORY;
    }
    int count = 0;

    while (has_more_rooms()) {
        if (count == capacity) {
            capacity *= 2;
            Room **tmp = realloc(room_array, sizeof(Room *) * capacity);
            if (!tmp) {
                free(room_array);
                return NO_MEMORY;
            }
            room_array = tmp;
        }

        DG_Room dg = get_next_room();
        Room *r = copy_room_from_datagen(&dg);
        if (!r) {
            free(room_array);
            return NO_MEMORY;
        }

        if (graph_insert(g, r) != GRAPH_STATUS_OK) {
            room_destroy(r);
            free(room_array);
            return NO_MEMORY;
        }

        room_array[count++] = r;
    }

    *room_array_out = room_array;
    *count_out = count;
    return OK;
}

static void connect_graph_edges(Graph *g, Room **room_array, int count)
{
    for (int i = 0; i < count; i++) {
        Room *r = room_array[i];
        for (int p = 0; p < r->portal_count; p++) {
            int target_id = r->portals[p].target_room_id;
            if (target_id >= 0) {
                Room key;
                key.id = target_id;
                Room *target = (Room *)graph_get_payload(g, &key);
                if (target != NULL) {
                    graph_connect(g, r, target);
                }
            }
        }
    }
}

Status loader_load_world(const char *config_file,
                         Graph **graph_out,
                         Room **first_room_out,
                         int *num_rooms_out,
                         Charset *charset_out)
{
    if (!config_file || !graph_out || !first_room_out || !num_rooms_out || !charset_out) {
        return INVALID_ARGUMENT;
    }
    *graph_out = NULL;
    *first_room_out = NULL;
    *num_rooms_out = 0;

    int dg_status = start_datagen(config_file);
    if (dg_status != DG_OK) {
        if (dg_status == DG_ERR_CONFIG) {
            return WL_ERR_CONFIG;
        }
        if (dg_status == DG_ERR_OOM) {
            return NO_MEMORY;
        }
        return WL_ERR_DATAGEN;
    }

    Graph *g = NULL;
    if (graph_create(compare_rooms, (GraphDestroyFn)room_destroy, &g) != GRAPH_STATUS_OK) {
        stop_datagen();
        return NO_MEMORY;
    }

    Room **room_array = NULL;
    int count = 0;
    Status s = load_rooms(g, &room_array, &count);
    if (s != OK) {
        graph_destroy(g);
        stop_datagen();
        return s;
    }

    connect_graph_edges(g, room_array, count);

    const DG_Charset *cs = dg_get_charset();
    if (cs) {
        charset_out->wall = cs->wall;
        charset_out->floor = cs->floor;
        charset_out->player = cs->player;
        charset_out->pushable = cs->pushable;
        charset_out->treasure = cs->treasure;
        charset_out->portal = cs->portal;
    }

    *graph_out = g;
    *first_room_out = (count > 0) ? room_array[0] : NULL;
    *num_rooms_out = count;

    free(room_array);
    stop_datagen();

    return OK;
}


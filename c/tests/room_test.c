#include <check.h>
#include <stdlib.h>
#include <string.h>
#include "room.h"

// Test room creation, dimensions, and floor grid
START_TEST(test_room_basics)
{
    Room *r = room_create(1, "TestRoom", 5, 5);
    ck_assert_ptr_nonnull(r);
    ck_assert_int_eq(room_get_width(r), 5);
    ck_assert_int_eq(room_get_height(r), 5);

    // Set floor grid (all walkable)
    bool *grid = malloc(sizeof(bool) * 25);
    for (int i = 0; i < 25; i++) grid[i] = true;
    ck_assert_int_eq(room_set_floor_grid(r, grid), OK);

    // Walkable check
    ck_assert(room_is_walkable(r, 0, 0));
    ck_assert(room_is_walkable(r, 4, 4));

    room_destroy(r);
}
END_TEST

// Test portals
START_TEST(test_room_portals)
{
    Room *r = room_create(2, "PortalRoom", 5, 5);

    Portal *portals = malloc(sizeof(Portal) * 1);
    portals[0].x = 2;
    portals[0].y = 3;
    portals[0].target_room_id = 99; // Corrected field name
    portals[0].name = strdup("Door99");

    ck_assert_int_eq(room_set_portals(r, portals, 1), OK);

    // Check portal destination
    ck_assert_int_eq(room_get_portal_destination(r, 2, 3), 99);

    room_destroy(r);
}
END_TEST




// Test getting starting position
START_TEST(test_room_start_position)
{
    Room *r = room_create(4, "StartRoom", 5, 5);

    // Add a portal, should be chosen first as start
    Portal *portals = malloc(sizeof(Portal) * 1);
    portals[0].x = 1;
    portals[0].y = 1;
    portals[0].target_room_id = 2; // Corrected field
    portals[0].name = strdup("Door");

    room_set_portals(r, portals, 1);

    int x = -1, y = -1;
    ck_assert_int_eq(room_get_start_position(r, &x, &y), OK);
    ck_assert_int_eq(x, 1);
    ck_assert_int_eq(y, 1);

    room_destroy(r);
}
END_TEST


// Keep your A1 tests, add these A2 tests:

START_TEST(test_room_get_id)
{
    Room *r = room_create(42, "TestRoom", 5, 5);
    ck_assert_int_eq(room_get_id(r), 42);
    
    ck_assert_int_eq(room_get_id(NULL), -1);
    
    room_destroy(r);
}
END_TEST


START_TEST(test_room_has_pushable_at)
{
    Room *r = room_create(1, "Room", 10, 10);
    
    // Create pushables
    r->pushables = malloc(sizeof(Pushable) * 2);
    r->pushables[0].x = 3;
    r->pushables[0].y = 4;
    r->pushables[1].x = 7;
    r->pushables[1].y = 8;
    r->pushable_count = 2;
    
    // Test finding pushables
    int idx = -1;
    ck_assert(room_has_pushable_at(r, 3, 4, &idx));
    ck_assert_int_eq(idx, 0);
    
    ck_assert(room_has_pushable_at(r, 7, 8, &idx));
    ck_assert_int_eq(idx, 1);
    
    // Test not finding pushable
    ck_assert(!room_has_pushable_at(r, 5, 5, &idx));
    
    // Test without idx output
    ck_assert(room_has_pushable_at(r, 3, 4, NULL));
    
    room_destroy(r);
}
END_TEST

START_TEST(test_room_try_push_success)
{
    Room *r = room_create(1, "Room", 10, 10);
    
    // Set up floor grid (all walkable)
    bool *grid = malloc(sizeof(bool) * 100);
    for (int i = 0; i < 100; i++) {
        grid[i] = true;
    }
    room_set_floor_grid(r, grid);
    
    // Create pushable at (5, 5)
    r->pushables = malloc(sizeof(Pushable));
    r->pushables[0].x = 5;
    r->pushables[0].y = 5;
    r->pushables[0].initial_x = 5;
    r->pushables[0].initial_y = 5;
    r->pushable_count = 1;
    
    // Push NORTH - should move to (5, 4)
    ck_assert_int_eq(room_try_push(r, 0, DIR_NORTH), OK);
    ck_assert_int_eq(r->pushables[0].x, 5);
    ck_assert_int_eq(r->pushables[0].y, 4);
    
    // Push EAST - should move to (6, 4)
    ck_assert_int_eq(room_try_push(r, 0, DIR_EAST), OK);
    ck_assert_int_eq(r->pushables[0].x, 6);
    ck_assert_int_eq(r->pushables[0].y, 4);
    
    room_destroy(r);
}
END_TEST

START_TEST(test_room_try_push_blocked_by_wall)
{
    Room *r = room_create(1, "Room", 10, 10);
    
    // Set up floor grid with wall at (5, 4)
    bool *grid = malloc(sizeof(bool) * 100);
    for (int i = 0; i < 100; i++) {
        grid[i] = true;
    }
    grid[4 * 10 + 5] = false;  // Wall at (5, 4)
    room_set_floor_grid(r, grid);
    
    // Create pushable at (5, 5)
    r->pushables = malloc(sizeof(Pushable));
    r->pushables[0].x = 5;
    r->pushables[0].y = 5;
    r->pushable_count = 1;
    
    // Try to push NORTH into wall - should fail
    ck_assert_int_eq(room_try_push(r, 0, DIR_NORTH), ROOM_IMPASSABLE);
    
    // Pushable should not have moved
    ck_assert_int_eq(r->pushables[0].x, 5);
    ck_assert_int_eq(r->pushables[0].y, 5);
    
    room_destroy(r);
}
END_TEST

START_TEST(test_room_try_push_blocked_by_another_pushable)
{
    Room *r = room_create(1, "Room", 10, 10);
    
    // All walkable
    bool *grid = malloc(sizeof(bool) * 100);
    for (int i = 0; i < 100; i++) {
        grid[i] = true;
    }
    room_set_floor_grid(r, grid);
    
    // Two pushables: one at (5, 5), one at (5, 4)
    r->pushables = malloc(sizeof(Pushable) * 2);
    r->pushables[0].x = 5;
    r->pushables[0].y = 5;
    r->pushables[1].x = 5;
    r->pushables[1].y = 4;
    r->pushable_count = 2;
    
    // Try to push first one NORTH into second one - should fail
    ck_assert_int_eq(room_try_push(r, 0, DIR_NORTH), ROOM_IMPASSABLE);
    
    // First pushable should not move
    ck_assert_int_eq(r->pushables[0].x, 5);
    ck_assert_int_eq(r->pushables[0].y, 5);
    
    room_destroy(r);
}
END_TEST

START_TEST(test_room_classify_tile_pushable)
{
    Room *r = room_create(1, "Room", 10, 10);
    
    // Set up floor
    bool *grid = malloc(sizeof(bool) * 100);
    for (int i = 0; i < 100; i++) {
        grid[i] = true;
    }
    room_set_floor_grid(r, grid);
    
    // Add pushable at (3, 3)
    r->pushables = malloc(sizeof(Pushable));
    r->pushables[0].x = 3;
    r->pushables[0].y = 3;
    r->pushable_count = 1;
    
    // Classify tile with pushable
    int id = -1;
    RoomTileType type = room_classify_tile(r, 3, 3, &id);
    ck_assert_int_eq(type, ROOM_TILE_PUSHABLE);
    ck_assert_int_eq(id, 0);  // Pushable index
    
    // Empty floor tile
    type = room_classify_tile(r, 5, 5, &id);
    ck_assert_int_eq(type, ROOM_TILE_FLOOR);
    
    room_destroy(r);
}
END_TEST

START_TEST(test_room_render_with_pushables)
{
    Room *r = room_create(1, "Room", 5, 5);
    
    // All walkable
    bool *grid = malloc(sizeof(bool) * 25);
    for (int i = 0; i < 25; i++) {
        grid[i] = true;
    }
    room_set_floor_grid(r, grid);
    
    // Add pushable at (2, 2)
    r->pushables = malloc(sizeof(Pushable));
    r->pushables[0].x = 2;
    r->pushables[0].y = 2;
    r->pushable_count = 1;
    
    // Render
    Charset cs = {.wall = '#', .floor = '.', .pushable = 'O'};
    char buffer[25];
    ck_assert_int_eq(room_render(r, &cs, buffer, 5, 5), OK);
    
    // Check pushable is rendered
    ck_assert_int_eq(buffer[2 * 5 + 2], 'O');
    
    room_destroy(r);
}
END_TEST



/*
START_TEST(test_room_render_skips_collected_treasures)
{
    Room *r = room_create(1, "Room", 5, 5);
    
    bool *grid = malloc(sizeof(bool) * 25);
    for (int i = 0; i < 25; i++) {
        grid[i] = true;
    }
    room_set_floor_grid(r, grid);
    
    // Add two treasures
    Treasure *treasures = malloc(sizeof(Treasure) * 2);
    treasures[0].id = 1;
    treasures[0].x = 1;
    treasures[0].y = 1;
    treasures[0].collected = false;  // Not collected
    
    treasures[1].id = 2;
    treasures[1].x = 3;
    treasures[1].y = 3;
    treasures[1].collected = true;   // Collected
    
    room_set_treasures(r, treasures, 2);
    
    // Render
    Charset cs = {.wall = '#', .floor = '.', .treasure = '$'};
    char buffer[25];
    room_render(r, &cs, buffer, 5, 5);
    
    // First treasure should be rendered
    ck_assert_int_eq(buffer[1 * 5 + 1], '$');
    
    // Second treasure should NOT be rendered (show floor instead)
    ck_assert_int_eq(buffer[3 * 5 + 3], '.');
    
    room_destroy(r);
}
END_TEST




START_TEST(test_room_pick_up_treasure)
{
    Room *r = room_create(1, "Room", 10, 10);
    
    // Add treasures
    Treasure *treasures = malloc(sizeof(Treasure) * 2);
    treasures[0].id = 100;
    treasures[0].collected = false;
    treasures[0].x = 5;
    treasures[0].y = 5;
    
    treasures[1].id = 200;
    treasures[1].collected = false;
    treasures[1].x = 6;
    treasures[1].y = 6;
    
    room_set_treasures(r, treasures, 2);
    
    // Pick up first treasure
    Treasure *picked = NULL;
    ck_assert_int_eq(room_pick_up_treasure(r, 100, &picked), OK);
    ck_assert_ptr_nonnull(picked);
    ck_assert_int_eq(picked->id, 100);
    ck_assert(picked->collected);
    
    // Try to pick up same treasure again - should fail
    Treasure *picked2 = NULL;
    ck_assert_int_eq(room_pick_up_treasure(r, 100, &picked2), INVALID_ARGUMENT);
    
    // Pick up second treasure
    ck_assert_int_eq(room_pick_up_treasure(r, 200, &picked), OK);
    ck_assert_int_eq(picked->id, 200);
    
    // Try non-existent treasure
    ck_assert_int_eq(room_pick_up_treasure(r, 999, &picked), ROOM_NOT_FOUND);
    
    room_destroy(r);
}
END_TEST

// Test treasure placement and retrieval
START_TEST(test_room_treasures)
{
    Room *r = room_create(3, "TreasureRoom", 5, 5);

    Treasure t;
    t.id = 42;
    t.x = 1;
    t.y = 2;
    t.name = strdup("Gold");

    ck_assert_int_eq(room_place_treasure(r, &t), OK);

    // Treasure ID at position
    ck_assert_int_eq(room_get_treasure_at(r, 1, 2), 42);

    room_destroy(r);
    free(t.name);
}
END_TEST

*/

Suite *my_room_suite(void)
{
    Suite *s = suite_create("roomTests");

    TCase *tc_basic = tcase_create("BasicA1");
    // Add your A1 tests here
    
    tcase_add_test(tc_basic, test_room_basics);
    tcase_add_test(tc_basic, test_room_portals);
    //tcase_add_test(tc_basic, test_room_treasures);
    tcase_add_test(tc_basic, test_room_start_position);
    suite_add_tcase(s, tc_basic);

    TCase *tc_a2 = tcase_create("A2Features");
    tcase_add_test(tc_a2, test_room_get_id);
    //tcase_add_test(tc_a2, test_room_pick_up_treasure);
    tcase_add_test(tc_a2, test_room_has_pushable_at);
    tcase_add_test(tc_a2, test_room_try_push_success);
    tcase_add_test(tc_a2, test_room_try_push_blocked_by_wall);
    tcase_add_test(tc_a2, test_room_try_push_blocked_by_another_pushable);
    tcase_add_test(tc_a2, test_room_classify_tile_pushable);
    tcase_add_test(tc_a2, test_room_render_with_pushables);
    //(tc_a2, test_room_render_skips_collected_treasures);
    suite_add_tcase(s, tc_a2);

    return s;
}

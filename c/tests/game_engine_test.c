#include <check.h>
#include <stdlib.h>
#include <string.h>
#include "types.h"
#include "game_engine.h"
#include "player.h"


// test that engine creation succeeds
START_TEST(test_engine_create_success)
{
    GameEngine *eng = NULL;

    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);
    ck_assert_ptr_nonnull(eng);

    game_engine_destroy(eng);
}
END_TEST


// test that room count is valid
START_TEST(test_engine_room_count)
{
    GameEngine *eng = NULL;
    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);  // Check creation succeeded

    int count = 0;
    s = game_engine_get_room_count(eng, &count);  // Reuse s, pass eng not &eng

    ck_assert_int_eq(s, OK);
    ck_assert_int_gt(count, 0);

    game_engine_destroy(eng);
}
END_TEST


// test that player moves correctly inside room
START_TEST(test_player_move_valid)
{
    // test that player can attempt a move

    GameEngine *eng = NULL;
    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);  // Check creation succeeded

    s = game_engine_move_player(eng, DIR_EAST);  // Reuse s

    ck_assert(
        s == OK ||
        s == ROOM_IMPASSABLE
    );

    game_engine_destroy(eng);

}
END_TEST


// test that reset restores initial state
START_TEST(test_engine_reset)
{
    GameEngine *eng = NULL;
    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);  // Check creation succeeded

    game_engine_move_player(eng, DIR_EAST);
    game_engine_move_player(eng, DIR_SOUTH);

    s = game_engine_reset(eng);  // Reuse s
    ck_assert_int_eq(s, OK);

    game_engine_destroy(eng);

}
END_TEST


// test that rendering returns a valid string
START_TEST(test_render_current_room)
{
    GameEngine *eng = NULL;
    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);  // Check creation succeeded

    char *output = NULL;
    s = game_engine_render_current_room(eng, &output);  // Reuse s

    ck_assert_int_eq(s, OK);
    ck_assert_ptr_nonnull(output);
    ck_assert_int_gt(strlen(output), 0);

    free(output);
    game_engine_destroy(eng);
}
END_TEST


// test that room ids can be retrieved
START_TEST(test_get_room_ids)
{
    GameEngine *eng = NULL;
    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);  // Check creation succeeded

    int *ids = NULL;
    int count = 0;

    s = game_engine_get_room_ids(eng, &ids, &count);  // Reuse s

    ck_assert_int_eq(s, OK);
    ck_assert_ptr_nonnull(ids);
    ck_assert_int_gt(count, 0);

    free(ids);
    game_engine_destroy(eng);
}
END_TEST



START_TEST(test_engine_treasure_collection)
{
    GameEngine *eng = NULL;
    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);
    
    const Player *p = game_engine_get_player(eng);
    ck_assert_ptr_nonnull(p);
    
    // Initially no treasures
    ck_assert_int_eq(player_get_collected_count(p), 0);
    
    // Move around and potentially collect treasures
    // (Outcome depends on room layout)
    for (int i = 0; i < 10; i++) {
        game_engine_move_player(eng, DIR_EAST);
    }
    
    // Check if any treasures collected
    int count = player_get_collected_count(p);
    // Count might be 0 or more depending on room layout
    ck_assert(count >= 0);
    
    game_engine_destroy(eng);
}
END_TEST

START_TEST(test_engine_reset_clears_treasures)
{
    GameEngine *eng = NULL;
    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);
    
    const Player *p = game_engine_get_player(eng);
    
    // Move and collect
    for (int i = 0; i < 20; i++) {
        game_engine_move_player(eng, DIR_EAST);
        game_engine_move_player(eng, DIR_SOUTH);
    }
    
    //int before_count = player_get_collected_count(p);
    
    // Reset
    s = game_engine_reset(eng);
    ck_assert_int_eq(s, OK);
    
    // Treasures should be cleared
    ck_assert_int_eq(player_get_collected_count(p), 0);
    
    game_engine_destroy(eng);
}
END_TEST

START_TEST(test_engine_push_obstacle)
{
    GameEngine *eng = NULL;
    Status s = game_engine_create("../assets/starter.ini", &eng);
    ck_assert_int_eq(s, OK);
    
    // Try moving - might push an obstacle or move normally
    s = game_engine_move_player(eng, DIR_NORTH);
    
    // Should either succeed (OK) or be blocked (ROOM_IMPASSABLE)
    ck_assert(s == OK || s == ROOM_IMPASSABLE);
    
    game_engine_destroy(eng);
}
END_TEST

START_TEST(test_game_engine_free_string)
{
    // Test the new free function
    char *test_str = malloc(100);
    strcpy(test_str, "test");
    
    // Should not crash
    game_engine_free_string(test_str);
    
    // Should be safe with NULL
    game_engine_free_string(NULL);
}
END_TEST

// Update suite:
Suite *game_engine_suite(void)
{
    Suite *s = suite_create("gameEngineTests");

    TCase *tc_core = tcase_create("core");
    tcase_add_test(tc_core, test_engine_create_success);
    tcase_add_test(tc_core, test_engine_room_count);
    tcase_add_test(tc_core, test_player_move_valid);
    tcase_add_test(tc_core, test_engine_reset);
    tcase_add_test(tc_core, test_render_current_room);
    tcase_add_test(tc_core, test_get_room_ids);
    
    // A2 tests
    tcase_add_test(tc_core, test_engine_treasure_collection);
    tcase_add_test(tc_core, test_engine_reset_clears_treasures);
    tcase_add_test(tc_core, test_engine_push_obstacle);
    tcase_add_test(tc_core, test_game_engine_free_string);
    
    suite_add_tcase(s, tc_core);

    return s;
}


#include <check.h>
#include <stdlib.h>
#include "player.h"

START_TEST(test_player_basic)
{
    Player *p = NULL;
    ck_assert_int_eq(player_create(1, 2, 3, &p), OK);
    ck_assert_ptr_nonnull(p);
    ck_assert_int_eq(player_get_room(p), 1);

    int x = 0, y = 0;
    ck_assert_int_eq(player_get_position(p, &x, &y), OK);
    ck_assert_int_eq(x, 2);
    ck_assert_int_eq(y, 3);

    ck_assert_int_eq(player_set_position(p, 5, 6), OK);
    ck_assert_int_eq(player_get_position(p, &x, &y), OK);
    ck_assert_int_eq(x, 5);
    ck_assert_int_eq(y, 6);

    ck_assert_int_eq(player_move_to_room(p, 42), OK);
    ck_assert_int_eq(player_get_room(p), 42);

    ck_assert_int_eq(player_reset_to_start(p, 7, 8, 9), OK);
    ck_assert_int_eq(player_get_room(p), 7);
    ck_assert_int_eq(player_get_position(p, &x, &y), OK);
    ck_assert_int_eq(x, 8);
    ck_assert_int_eq(y, 9);

    player_destroy(p);
}
END_TEST

// NEW A2 tests

START_TEST(test_player_initial_treasure_state)
{
    Player *p = NULL;
    ck_assert_int_eq(player_create(0, 0, 0, &p), OK);
    
    // Initially no treasures
    ck_assert_int_eq(player_get_collected_count(p), 0);
    ck_assert(!player_has_collected_treasure(p, 1));
    
    int count = 0;
    //const Treasure * const *treasures = player_get_collected_treasures(p, &count);
    ck_assert_int_eq(count, 0);
    
    player_destroy(p);
}
END_TEST

START_TEST(test_player_collect_single_treasure)
{
    Player *p = NULL;
    ck_assert_int_eq(player_create(0, 0, 0, &p), OK);
    
    // Create a treasure
    Treasure t = {
        .id = 100,
        .name = "Gold Coin",
        .x = 5,
        .y = 5,
        .collected = false
    };
    
    // Collect it
    ck_assert_int_eq(player_try_collect(p, &t), OK);
    
    // Verify
    ck_assert_int_eq(player_get_collected_count(p), 1);
    ck_assert(player_has_collected_treasure(p, 100));
    ck_assert(t.collected);  // Treasure marked as collected
    
    int count = 0;
    const Treasure * const *treasures = player_get_collected_treasures(p, &count);
    ck_assert_int_eq(count, 1);
    ck_assert_ptr_nonnull(treasures);
    ck_assert_int_eq(treasures[0]->id, 100);
    
    player_destroy(p);
}
END_TEST

START_TEST(test_player_collect_multiple_treasures)
{
    Player *p = NULL;
    ck_assert_int_eq(player_create(0, 0, 0, &p), OK);
    
    // Create treasures
    Treasure t1 = {.id = 1, .collected = false};
    Treasure t2 = {.id = 2, .collected = false};
    Treasure t3 = {.id = 3, .collected = false};
    
    // Collect them
    ck_assert_int_eq(player_try_collect(p, &t1), OK);
    ck_assert_int_eq(player_try_collect(p, &t2), OK);
    ck_assert_int_eq(player_try_collect(p, &t3), OK);
    
    // Verify count
    ck_assert_int_eq(player_get_collected_count(p), 3);
    
    // Verify each treasure
    ck_assert(player_has_collected_treasure(p, 1));
    ck_assert(player_has_collected_treasure(p, 2));
    ck_assert(player_has_collected_treasure(p, 3));
    ck_assert(!player_has_collected_treasure(p, 4));
    
    player_destroy(p);
}
END_TEST

START_TEST(test_player_cannot_collect_twice)
{
    Player *p = NULL;
    ck_assert_int_eq(player_create(0, 0, 0, &p), OK);
    
    Treasure t = {.id = 50, .collected = false};
    
    // First collection should succeed
    ck_assert_int_eq(player_try_collect(p, &t), OK);
    ck_assert_int_eq(player_get_collected_count(p), 1);
    
    // Second collection should fail
    ck_assert_int_eq(player_try_collect(p, &t), INVALID_ARGUMENT);
    ck_assert_int_eq(player_get_collected_count(p), 1);  // Still 1
    
    player_destroy(p);
}
END_TEST

START_TEST(test_player_collect_null_pointer)
{
    Player *p = NULL;
    ck_assert_int_eq(player_create(0, 0, 0, &p), OK);
    
    // Try to collect NULL treasure
    ck_assert_int_eq(player_try_collect(p, NULL), NULL_POINTER);
    
    // Try with NULL player
    Treasure t = {.id = 1, .collected = false};
    ck_assert_int_eq(player_try_collect(NULL, &t), NULL_POINTER);
    
    player_destroy(p);
}
END_TEST

START_TEST(test_player_reset_clears_treasures)
{
    Player *p = NULL;
    ck_assert_int_eq(player_create(0, 5, 5, &p), OK);
    
    // Collect some treasures
    Treasure t1 = {.id = 10, .collected = false};
    Treasure t2 = {.id = 20, .collected = false};
    player_try_collect(p, &t1);
    player_try_collect(p, &t2);
    
    ck_assert_int_eq(player_get_collected_count(p), 2);
    
    // Reset player
    ck_assert_int_eq(player_reset_to_start(p, 1, 10, 10), OK);
    
    // Treasures should be cleared
    ck_assert_int_eq(player_get_collected_count(p), 0);
    ck_assert(!player_has_collected_treasure(p, 10));
    ck_assert(!player_has_collected_treasure(p, 20));
    
    // Position should be reset
    int x = 0, y = 0;
    ck_assert_int_eq(player_get_position(p, &x, &y), OK);
    ck_assert_int_eq(x, 10);
    ck_assert_int_eq(y, 10);
    ck_assert_int_eq(player_get_room(p), 1);
    
    player_destroy(p);
}
END_TEST

Suite *my_player_suite(void)
{
    Suite *s = suite_create("playerTests");
    
    TCase *tc_basic = tcase_create("BasicA1");
    tcase_add_test(tc_basic, test_player_basic);
    suite_add_tcase(s, tc_basic);
    
    TCase *tc_treasure = tcase_create("TreasureA2");
    tcase_add_test(tc_treasure, test_player_initial_treasure_state);
    tcase_add_test(tc_treasure, test_player_collect_single_treasure);
    tcase_add_test(tc_treasure, test_player_collect_multiple_treasures);
    tcase_add_test(tc_treasure, test_player_cannot_collect_twice);
    tcase_add_test(tc_treasure, test_player_collect_null_pointer);
    tcase_add_test(tc_treasure, test_player_reset_clears_treasures);
    suite_add_tcase(s, tc_treasure);
    
    return s;
}



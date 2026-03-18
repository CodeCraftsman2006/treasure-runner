#include <check.h>
#include <stdlib.h>
#include "world_loader.h"
#include "graph.h"
#include "room.h"

// test that loading a valid world succeeds
START_TEST(test_load_world_success)
{
    Graph *g = NULL;
    Room *first = NULL;
    int num_rooms = 0;
    Charset cs = {0};

    Status s = loader_load_world("../assets/starter.ini", &g, &first, &num_rooms, &cs);
    ck_assert_int_eq(s, OK);
    ck_assert_ptr_nonnull(g);
    ck_assert_ptr_nonnull(first);
    ck_assert_int_gt(num_rooms, 0);
    
    graph_destroy(g);
} 
END_TEST

// test that invalid config returns an error
START_TEST(test_load_world_invalid_config)
{
    Graph *g = NULL;
    Room *first = NULL;
    int num_rooms = 0;
    Charset cs = {0};

    // Use an INVALID file path - this file doesn't exist
    Status s = loader_load_world("nonexistent_file.ini", &g, &first, &num_rooms, &cs);
    
    // Should return an error (either WL_ERR_CONFIG or WL_ERR_DATAGEN)
    ck_assert(s == WL_ERR_CONFIG || s == WL_ERR_DATAGEN);
    ck_assert_ptr_null(g);
    ck_assert_ptr_null(first);
    ck_assert_int_eq(num_rooms, 0);
} 
END_TEST

// test that deep copy works (datagen can be freed)
START_TEST(test_deep_copy)
{
    Graph *g = NULL;
    Room *first = NULL;
    int num_rooms = 0;
    Charset cs = {0};

    Status s = loader_load_world("../assets/starter.ini", &g, &first, &num_rooms, &cs);
    ck_assert_int_eq(s, OK);

    // The loaded room and graph should remain intact even after datagen is freed
    // (which happens inside loader_load_world)
    int node_count = graph_size(g);
    ck_assert_int_eq(node_count, num_rooms);

    graph_destroy(g);
} 
END_TEST

// suite definition
Suite *my_world_loader_suite(void)
{
    Suite *s = suite_create("worldLoaderTests");

    TCase *tc_core = tcase_create("core");
    tcase_add_test(tc_core, test_load_world_success);
    tcase_add_test(tc_core, test_load_world_invalid_config);
    tcase_add_test(tc_core, test_deep_copy);
    suite_add_tcase(s, tc_core);

    return s;
}
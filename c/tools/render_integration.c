/*
 *
 * Tests room rendering with the refactored game engine:
 * 1. Creates a GameEngine instance with the config file
 * 2. Renders the player's current room
 * 3. Displays room metadata (width, height, entities)
 * 4. Prints the rendered room to stdout
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "game_engine.h"
#include "player.h"
#include "types.h"

static void measure_room_dimensions(const char *room_str,
                                    int *width_out,
                                    int *height_out)
{
    int width = 0;
    int height = 0;

    if (room_str) {
        while (room_str[width] && room_str[width] != '\n') {
            width++;
        }
        for (const char *cursor = room_str; *cursor; cursor++) {
            if (*cursor == '\n') {
                height++;
            }
        }
        if (height == 0 && width > 0) {
            height = 1;
        }
    }

    *width_out = width;
    *height_out = height;
}

static Status render_and_print_room(const GameEngine *engine, int room_id)
{
    char *room_str = NULL;
    Status status = game_engine_render_room(engine, room_id, &room_str);
    if (status != OK) {
        return status;
    }

    int width = 0;
    int height = 0;
    measure_room_dimensions(room_str, &width, &height);

    printf("====================================\n");
    printf("Room %d - %dx%d\n", room_id, width, height);
    printf("====================================\n");

    if (room_str) {
        printf("%s\n", room_str);
        free(room_str);
    }

    return OK;
}

int main(int argc, char *argv[])
{
    const char *config_path = argc > 1 ? argv[1] : "assets/treasure_runner.ini";

    printf("=== Treasure Runner Game Engine Rendering Test ===\n\n");
    printf("Loading game from: %s\n\n", config_path);

    /* Create game engine (loads world, charset, player) */
    GameEngine *engine = NULL;
    Status status = game_engine_create(config_path, &engine);
    if (status != OK || !engine) {
        (void)fprintf(stderr, "ERROR: Failed to create game engine\n");
        (void)fprintf(stderr, "Make sure config path is correct: %s\n", config_path);
        return EXIT_FAILURE;
    }

    printf("✓ Game engine created successfully\n");

    /* Get room count */
    int room_count = 0;
    status = game_engine_get_room_count(engine, &room_count);
    if (status != OK) {
        (void)fprintf(stderr, "ERROR: Failed to get room count (status=%d)\n", status);
        game_engine_destroy(engine);
        return EXIT_FAILURE;
    }
    printf("✓ Found %d rooms in world\n\n", room_count);

    /* Get player reference */
    const Player *player = game_engine_get_player(engine);
    if (!player) {
        (void)fprintf(stderr, "ERROR: Failed to get player\n");
        game_engine_destroy(engine);
        return EXIT_FAILURE;
    }

    int player_room = player_get_room(player);
    int player_x = 0;
    int player_y = 0;
    Status pos_status = player_get_position(player, &player_x, &player_y);
    if (pos_status != OK) {
        (void)fprintf(stderr, "ERROR: Failed to get player position\n");
        game_engine_destroy(engine);
        return EXIT_FAILURE;
    }

    printf("✓ Player created in room %d at position (%d, %d)\n", player_room, player_x, player_y);
    printf("\n");

    int *room_ids = NULL;
    int id_count = 0;
    status = game_engine_get_room_ids(engine, &room_ids, &id_count);
    if (status != OK || !room_ids) {
        (void)fprintf(stderr, "ERROR: Failed to retrieve room IDs (status=%d)\n", status);
        game_engine_destroy(engine);
        return EXIT_FAILURE;
    }

    for (int i = 0; i < id_count; i++) {
        int room_id = room_ids[i];
        status = render_and_print_room(engine, room_id);
        if (status != OK) {
            (void)fprintf(stderr,
                          "ERROR: Failed to render room %d (status=%d)\n",
                          room_id,
                          status);
            free(room_ids);
            game_engine_destroy(engine);
            return EXIT_FAILURE;
        }
    }

    free(room_ids);

    printf("====================================\n");
    printf("✓ Rendering test complete\n");

    /* Cleanup */
    game_engine_destroy(engine);

    return EXIT_SUCCESS;
}

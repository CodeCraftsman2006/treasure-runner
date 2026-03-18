// puzzlegen_demo.c
// Demonstrates usage of the datagen library (libpuzzlegen.so) and datagen.h
// Usage: ./puzzlegen_demo <path_to_ini_file>

#include <stdio.h>
#include <stdlib.h>

#include "datagen.h"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <path_to_ini_file>\n", argv[0]);
        return 1;
    }
    const char *ini_path = argv[1];

    int status = start_datagen(ini_path);
    if (status != 0) {
        fprintf(stderr, "Failed to initialize datagen (error %d).\n", status);
        return 1;
    }

    printf("Rooms in %s:\n", ini_path);
    int room_idx = 0;
    while (has_more_rooms()) {
        DG_Room room = get_next_room();
        printf("Room #%d\n", room_idx);
        printf("  ID: %d\n", room.id);
        printf("  Size: %dx%d\n", room.width, room.height);
        printf("  Portals: %d\n", room.portal_count);
        printf("  Pushables: %d\n", room.pushable_count);
        printf("  Treasures: %d\n", room.treasure_count);
        printf("  Switches: %d\n", room.switch_count);
        printf("--------------------------\n");
        room_idx++;
    }

    stop_datagen();
    return 0;
}

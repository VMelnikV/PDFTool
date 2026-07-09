#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    // Отримуємо шлях до поточного виконуваного файлу
    char script_path[1024];
    strncpy(script_path, argv[0], sizeof(script_path) - 1);
    script_path[sizeof(script_path) - 1] = '\0';
    
    // Знаходимо останній слеш і відрізаємо ім'я файлу
    char *last_slash = strrchr(script_path, '/');
    if (last_slash) {
        *(last_slash + 1) = '\0';
    } else {
        script_path[0] = '\0';
    }
    
    // Будуємо шлях до обгортки
    char wrapper_path[1024];
    snprintf(wrapper_path, sizeof(wrapper_path), "%sapprun.sh", script_path);
    
    // Запускаємо apprun.sh з тими ж аргументами
    char *args[argc + 2];
    args[0] = "/bin/bash";
    args[1] = wrapper_path;
    for (int i = 1; i < argc; i++) {
        args[i + 1] = argv[i];
    }
    args[argc + 1] = NULL;
    
    execv("/bin/bash", args);
    
    // Якщо execv повернувся - помилка
    perror("Помилка запуску");
    return 1;
}

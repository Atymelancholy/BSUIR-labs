package com.example.bookblog.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/logs")
@Tag(name = "Log Controller", description = "Асинхронное создание и получение лог-файлов")
public class Log {

    private static final String LOG_FILE_PATH = "logs/application.log";
    private static final String TEMP_DIR = System.getProperty("java.io.tmpdir");
    private static final Map<String, String> taskStatusMap = new ConcurrentHashMap<>();
    private static final Map<String, String> taskFileMap = new ConcurrentHashMap<>();
    private static final ExecutorService executor = Executors.newFixedThreadPool(4);

    @Operation(summary = "Создать лог-файл", description = "Асинхронное создание лог-файла")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "202", description = "Задача на создание принята"),
    })
    @PostMapping("/create")
    public ResponseEntity<Map<String, String>> createLogFile() {
        String taskId = UUID.randomUUID().toString();
        taskStatusMap.put(taskId, "PENDING");

        executor.submit(() -> {
            try {
                Thread.sleep(10000); // задержка 10 сек
                taskStatusMap.put(taskId, "PROCESSING");

                Path sourcePath = Paths.get(LOG_FILE_PATH);
                if (!Files.exists(sourcePath)) {
                    taskStatusMap.put(taskId, "ERROR: Source log file not found");
                    return;
                }

                String tempFileName = "log_" + taskId + ".log";
                Path tempFilePath = Paths.get(TEMP_DIR, tempFileName);
                Files.copy(sourcePath, tempFilePath);

                taskFileMap.put(taskId, tempFilePath.toString());
                taskStatusMap.put(taskId, "COMPLETED");
            } catch (Exception e) {
                taskStatusMap.put(taskId, "ERROR: " + e.getMessage());
            }
        });

        return ResponseEntity.accepted().body(Map.of(
                "task_id", taskId,
                "status", "PENDING"
        ));
    }

    @Operation(summary = "Проверить статус", description = "Проверить статус создания лог-файла")
    @GetMapping("/status/{taskId}")
    public ResponseEntity<Map<String, String>> getTaskStatus(@PathVariable String taskId) {
        String status = taskStatusMap.get(taskId);
        if (status == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(Map.of("task_id", taskId, "status", status));
    }

    @Operation(summary = "Скачать лог-файл", description = "Получить созданный лог-файл")
    @GetMapping("/download/{taskId}")
    public ResponseEntity<?> downloadLogFile(@PathVariable String taskId) throws IOException {
        String status = taskStatusMap.get(taskId);
        if (status == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Задача с указанным ID не найдена"));
        }

        if (!"COMPLETED".equals(status)) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", "Файл ещё не готов к загрузке. Текущий статус: " + status));
        }

        String filePath = taskFileMap.get(taskId);
        if (filePath == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Файл не найден"));
        }

        Path path = Paths.get(filePath);
        Resource resource = new UrlResource(path.toUri());
        if (!resource.exists() || !resource.isReadable()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", "Файл не существует или недоступен"));
        }

        return ResponseEntity.ok()
                .contentType(MediaType.TEXT_PLAIN)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + resource.getFilename() + "\"")
                .body(resource);
    }
}

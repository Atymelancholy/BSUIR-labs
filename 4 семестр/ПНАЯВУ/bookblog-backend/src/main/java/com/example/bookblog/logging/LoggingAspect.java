package com.example.bookblog.logging;

import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.AfterReturning;
import org.aspectj.lang.annotation.AfterThrowing;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class LoggingAspect {
    private static final Logger logger = LoggerFactory.getLogger(LoggingAspect.class);

    @Before("execution(* com.example.bookblog.controller.*.*(..))")
    public void logBefore(JoinPoint joinPoint) {
        logger.info("Вход в метод контроллера: {} с аргументами: {}",
                joinPoint.getSignature().toShortString(), joinPoint.getArgs());
    }

    @AfterReturning(pointcut = "execution(* com.example.bookblog.controller.*.*(..))",
            returning = "result")
    public void logAfterReturning(JoinPoint joinPoint, Object result) {
        logger.info("Выход из метода контроллера: {} с результатом: {}",
                joinPoint.getSignature().toShortString(), result);
    }

    @AfterThrowing(pointcut = "execution(* com.example.bookblog.controller.*.*(..))",
            throwing = "error")
    public void logAfterThrowing(JoinPoint joinPoint, Throwable error) {
        logger.error("Ошибка в методе контроллера: {} с причиной: {}",
                joinPoint.getSignature().toShortString(), error.getMessage());
    }

    @AfterThrowing(pointcut = "execution(* com.example.bookblog.service.*.findById(..))",
            throwing = "error")
    public void logNotFound(JoinPoint joinPoint, Throwable error) {
        logger.warn("Объект не найден: {} с аргументами: {}",
                joinPoint.getSignature().toShortString(), joinPoint.getArgs());
    }

    @AfterThrowing(pointcut = "execution(* com.example.bookblog.service.*.delete(..))",
            throwing = "error")
    public void logDeleteNotFound(JoinPoint joinPoint, Throwable error) {
        logger.warn("Попытка удалить несуществующий объект: {} с аргументами: {}",
                joinPoint.getSignature().toShortString(), joinPoint.getArgs());
    }

    @AfterThrowing(pointcut = "execution(* com.example.bookblog.service.*.save(..))",
            throwing = "error")
    public void logDuplicateSave(JoinPoint joinPoint, Throwable error) {
        logger.warn("Попытка создать дубликат объекта: {} с аргументами: {}",
                joinPoint.getSignature().toShortString(), joinPoint.getArgs());
    }

    @Before("execution(* com.example.bookblog.cache.*.*(..))")
    public void logCacheOperations(JoinPoint joinPoint) {
        logger.info("Операция с кэшем: {} с аргументами: {}",
                joinPoint.getSignature().toShortString(), joinPoint.getArgs());
    }

    @AfterReturning(pointcut = "execution(* com.example.bookblog.cache.InMemoryCache.put(..))")
    public void logCachePut(JoinPoint joinPoint) {
        logger.info("Добавление в кэш: {} с аргументами: {}",
                joinPoint.getSignature().toShortString(), joinPoint.getArgs());
    }

    @AfterReturning(pointcut = "execution(* com.example.bookblog.cache.InMemoryCache.remove(..))")
    public void logCacheRemove(JoinPoint joinPoint) {
        logger.info("Удаление из кэша: {} с аргументами: {}",
                joinPoint.getSignature().toShortString(), joinPoint.getArgs());
    }

    @AfterReturning(pointcut = "execution(* com.example.bookblog.cache.InMemoryCache.get(..))",
            returning = "result")
    public void logCacheGet(JoinPoint joinPoint, Object result) {
        logger.info("Чтение из кэша: {} с аргументами: {}, результат: {}",
                joinPoint.getSignature().toShortString(), joinPoint.getArgs(), result);
    }

    @AfterReturning(pointcut = "execution(* com.example.bookblog.cache.InMemoryCache.clear(..))")
    public void logCacheClear(JoinPoint joinPoint) {
        logger.info("Очистка кэша: {}", joinPoint.getSignature().toShortString());
    }
}
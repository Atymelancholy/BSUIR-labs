#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

class QStackedWidget;
class PCIWindow;
class ATAWindow;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = 0);
    ~MainWindow();

private slots:
    void showPCIScanner();
    void showATAScanner();
    void returnToHome();

private:
    void setupUI();
    void setupStyles();
    void createHomeScreen();
    void createPCIScreen();
    void createATAScreen();

    QStackedWidget *stackedWidget;
    QWidget *homeScreen;
    PCIWindow *pciScreen;
    ATAWindow *ataScreen;
};

#endif

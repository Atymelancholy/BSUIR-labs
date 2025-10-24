#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

namespace Ui {
class MainWindow;
}

class Lab1Window;
class QLabel;
class QPushButton;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

protected:
    void resizeEvent(QResizeEvent *event) override;

private slots:
    void onPigButtonClicked();
    void showLab1Window();
    void backToMain();

private:
    Ui::MainWindow *ui;
    void setupBackground();
    void setupUI();
    void positionElements();

    Lab1Window *m_lab1Window;
    QLabel *characterImageLabel;
    QLabel *pigImageLabel;     // Картинка свинки
    QLabel *titleLabel;
    QPushButton *pigButton;    // Кнопка поверх свинки
};

#endif // MAINWINDOW_H

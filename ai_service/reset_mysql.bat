@echo off
echo ========================================
echo MySQL Password Reset Script
echo ========================================
echo.

echo Step 1: Stopping MySQL service...
net stop MySQL80 /Y 2>nul
net stop MySQL /Y 2>nul
echo Done.
echo.

echo Step 2: Starting MySQL in safe mode with skip-grants...
START "" /B "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysqld.exe" --skip-grant-tables --skip-networking
echo Waiting 5 seconds for MySQL to start...
timeout /t 5 /nobreak >nul
echo Done.
echo.

echo Step 3: Resetting root password to empty...
echo Please run this command in a new terminal:
echo.
echo "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysql.exe" -u root
echo.
echo Then run these SQL commands:
echo.
echo USE mysql;
echo ALTER USER 'root'@'localhost' IDENTIFIED BY '';
echo FLUSH PRIVILEGES;
echo EXIT;
echo.
echo After resetting, come back here and press any key to continue...
pause >nul

echo.
echo Step 4: Stopping safe mode MySQL...
taskkill /F /IM mysqld.exe 2>nul
echo Done.
echo.

echo Step 5: Restarting MySQL service...
net start MySQL80 /Y 2>nul
net start MySQL /Y 2>nul
echo Done.
echo.

echo ========================================
echo Password reset complete!
echo Now you can connect with: mysql -u root
echo ========================================
pause

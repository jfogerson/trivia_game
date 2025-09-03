@echo off
REM Check if a commit message was provided
IF "%~1"=="" (
    echo Please provide a commit message.
    echo Usage: git_commit_push.bat "Your descriptive commit message"
    exit /b 1
)

REM Combine all arguments into a single commit message
SET commitMessage=%~1
SHIFT
:loop
IF "%~1"=="" GOTO continue
SET commitMessage=%commitMessage% %~1
SHIFT
GOTO loop

:continue
echo Committing with message: "%commitMessage%"
git add .
git commit -m "%commitMessage%"
git push origin main
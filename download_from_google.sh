#!/bin/bash

cd /home/kali/Playground/league_of_legends/2023/

wget -q "https://drive.google.com/uc?export=download&id=1XXk2LO0CsNADBB1LRGOV5rUpyZdEZ8s2" -O 2023.csv

sleep 3

{ head -1 2023.csv; grep -e ",LEC," 2023.csv; } > LEC.csv
{ head -1 2023.csv; grep -e ",LCS," 2023.csv; } > LCS.csv
{ head -1 2023.csv; grep -e ",LCK," 2023.csv; } > LCK.csv
{ head -1 2023.csv; grep -e ",LPL," 2023.csv; } > LPL.csv

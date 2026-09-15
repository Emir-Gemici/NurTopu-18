#!/usr/bin/env bash
# Navitas Harita Stüdyosu'nu açar — çift tıkla ya da masaüstü/menü kısayoluyla.
cd "$(dirname "$0")"
exec ../.venv/bin/python harita_studyo.py

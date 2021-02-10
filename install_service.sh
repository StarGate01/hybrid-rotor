#!/bin/bash

sudo cp hybrid-rotor.service /etc/systemd/system/hybrid-rotor.service
sudo chmod 644 /etc/systemd/system/hybrid-rotor.service

sudo systemctl daemon-reload

sudo systemctl enable hybrid-rotor
sudo systemctl start hybrid-rotor
sudo systemctl status hybrid-rotor

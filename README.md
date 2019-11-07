# openvpn-route53-dns
Service that scrapes a local openvpn server client config directory (CCD)  and makes dns entries in route53 for each common-name

Requirements:
- pipenv
- python3.7+

To use, checkout repo and run `pipenv install` to create a virtual environment and install requirements.
Modify the edge-dns.service file to point to the python virtual environment created by pipenv, 
you can get this information by using the `pipenv --venv` command to print the virtual environment home.
Copy the modified edge-dns.service file to the /etc/systemd/system folder and run `sudo systemctl daemon-reload` then 
`sudo systemctl enable edge-dns` and `sudo systemctl start edge-dns` 

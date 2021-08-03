take-home-test
--------------

Script requires `boto3, pyyaml and argparse`.
For configuration replace the `ssh_key` value for users in `config.yml` with public keys that correspond to your private keys.  

virtual environment setup
-------------------------
- `python3 -m venv script`
- `source script/bin/activate`
- `pip install -r requirements.txt`

execute
-------
- `chmod +x ./launch_ec2.py`
- `./launch_ec2.py` Will attempt to launch into a default VPC if present.
- An optional subnet can be specified with `-s <subnetid>`.
- By default the script expects a yaml file in the current directory named `config.yml`. One can optionally be specified with `-c <yaml file path>`
- You may then login as the users specified in the config using your private keys. You may need to adjust the security group attached to the instance to allow ssh access on port 22.
- `deactivate` 

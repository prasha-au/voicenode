$ip = $args[0]
if (-not $ip) {
	throw "IP address parameter is required."
}

# Check if setup folder exists on remote host
$remotePath = "~/setup"
$initialSetupCompleted = ssh voicenode@$ip "[ -f $remotePath/completed ] && echo 1 || echo 0"
Write-Host "Initial setup completed? $initialSetupCompleted"
if ($initialSetupCompleted -eq "0") {
	scp $PSScriptRoot/setup.sh $PSScriptRoot/config.txt voicenode@${ip}:$remotePath
	ssh voicenode@$ip "bash $remotePath/setup.sh"
	Write-Host "Initial setup has been completed. Device will reboot soon and you can run this again."
	Exit
}

# Copy the image over
Write-Host "Transferring Docker image..."
docker save voicenode | ssh voicenode@$ip "docker load"
Write-Host "Restarting container..."
ssh voicenode@$ip "docker rm -f voicenode || true && docker run -d --restart unless-stopped --name voicenode --net=host --privileged -v /dev:/dev voicenode"

ssh voicenode@$ip "sudo docker logs -f voicenode"

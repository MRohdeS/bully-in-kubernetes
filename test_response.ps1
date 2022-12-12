#Run a load test towards your Kubernetes cluster and note down the response times in hours:seconds:milliseconds. 
#using PowerShell to make a simple loop that sends a lot of HTTP requests to your endpoint rapidly and saves the response times individually.

#Create the bully_response.txt file
New-Item -Path . -Name bully_response.txt -ItemType File -Force

#Create a variable to store the response times
$responsetimes = @()

#Loop 1000 times and send a HTTP request to the bully-app service
for ($i = 0; $i -lt 1000; $i++) {
    $responsetimes += (Invoke-WebRequest -Uri http://127.0.0.1:55578/ | Measure-Object TotalMilliseconds)
    Write-Host "Response time: $responsetimes[$i]ms"
}

#Write the response times to a file
$responsetimes | Out-File bully_response.txt

#Read the bully_response.txt file and print the response times
Get-Content bully_response.txt

#Delete the bully_response.txt file
Remove-Item bully_response.txt
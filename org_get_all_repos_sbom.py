# Imports
import requests
import os
import json
import csv
import time

###
## Introduction
###
print("##################################################")
print("Finding all repos' SBOMs and storing in CSV")
print("The CSV will be stored as an artifact in the GitHub Actions run")
print("##################################################")

###
## Functions
###

# Make sure all initial vars are present
def initial_var_validation():
  # Get env variable GITHUB_TOKEN, and if not present, exit
  if 'GITHUB_TOKEN' not in os.environ:
    print("GITHUB_TOKEN not found in environment variables")
    exit(1)
  # Read repo we should evluate as an environmental var
  if 'GITHUB_ORG' not in os.environ:
    print("GITHUB_ORG not found in environment variables")
    exit(1)
  return True

# Check if hitting API rate-limiting
def hold_until_rate_limit_success():
  while True:
    response = requests.get(
      url="https://api.github.com/rate_limit",
      headers={
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"
      }
    )

    if response.status_code != 200:
      print("Error fetching rate limit info")
      exit(1)

    rate_limit_info = response.json()
    remaining = rate_limit_info['rate']['remaining']

    if remaining < 100:
      print("ℹ️  We have less than 100 GitHub API rate-limit tokens left, sleeping for 1 minute and checking again")
      time.sleep(60)
    else:
      break

# Initialize CSV
def initialize_csv():
  with open(GITHUB_ORG+"_repo_dependency_licensing.csv", 'w', newline='') as file:
    # Initialize writer
    writer = csv.writer(file)
    
    # Write header
    field = ["org", "repo", "dependency_name", "license"]
    writer.writerow(field)

# Build headers
def build_headers():
  # Create headers for sbom request
  headers = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": "Bearer "+GITHUB_TOKEN,
    }
  return headers

# Find count of all repos in org and store as var
def get_repo_count():
  # Get API token wallet
  hold_until_rate_limit_success()
  
  # Find how many repos exist in the Org
  org_info = requests.get(
    url="https://api.github.com/orgs/"+GITHUB_ORG,
    headers=headers
    )

  # Check response code, and if not 200, exit
  if org_info.status_code != 200:
    print("Error fetching org info")
    exit(1)

  # Store info
  PRIVATE_REPO_COUNT=org_info.json()['owned_private_repos']
  PUBLIC_REPO_COUNT=org_info.json()['public_repos']
  TOTAL_REPO_COUNT=PRIVATE_REPO_COUNT+PUBLIC_REPO_COUNT

  # Print out the number of repos found
  # print("Number of public repos found in org: "+str(PUBLIC_REPO_COUNT))
  # print("Number of private repos found in org: "+str(PRIVATE_REPO_COUNT))
  # print("Total number of repos found in org: "+str(TOTAL_REPO_COUNT))

  # Build dict of info and return
  d = dict(); 
  d['PRIVATE_REPO_COUNT'] = PRIVATE_REPO_COUNT
  d['PUBLIC_REPO_COUNT'] = PUBLIC_REPO_COUNT
  d['TOTAL_REPO_COUNT'] = TOTAL_REPO_COUNT
  return d 

# Get all repo information
def get_all_repo_names():
  
  # Check API token wallet
  hold_until_rate_limit_success()
  
  repo_count_info = get_repo_count()

  # Can get 100 repos at a time, so need to loop over all repos
  repos = []
  
  # Announce
  print()
  print("Fetching all repos")

  per_page=100
  for i in range(1, repo_count_info["TOTAL_REPO_COUNT"]//100+2):
    print("Fetching repos page "+str(i))
    
    # Fetch all repos
    response = requests.get(
      url="https://api.github.com/orgs/"+GITHUB_ORG+"/repos?per_page="+str(per_page)+"+&page="+str(i),
      headers=headers
      )

    # Check response code, and if not 200, exit
    if response.status_code != 200:
      print("Error fetching repos")
      exit(1)

    # Iterate over response, find all repos
    for repo in response.json():
      # If not archived, disabled, or template, append
      if repo["archived"] == False and repo["disabled"] == False and repo["is_template"] == False:
        repos.append(repo["name"])

  # Announce
  print()

  return repos

# Get dependencies for repo
def get_repo_dependencies(repo, index, repo_count):

  # Check rate limit
  hold_until_rate_limit_success()
  
  # URL
  url = "https://api.github.com/repos/"+GITHUB_ORG+"/"+repo+"/dependency-graph/sbom"

  # Fetch sbom
  response = requests.get(
    url=url,
    headers=headers
    )

  # Check response code, and if not 200, exit
  if response.status_code == 200:
    # Print green check box
    print("✅ Successfully fetched SBOM for repo", repo, "("+str(index)+"/"+str(repo_count)+")")
  else:
    print("❌ Error fetching SBOM for repo", repo, "("+str(index)+"/"+str(repo_count)+")")
    # Print error message
    print("Error message:", response.json()['message'])
    return

  # Parse response by looping over sbom.packages to get all names and license types
  for package in response.json()['sbom']['packages']:
    # If license key not present, set to unknown
    if 'licenseConcluded' not in package:
      license = "Unknown"
    else:
      license = package['licenseConcluded']

    # If license contains string GPL, print out repo name
    if "GPL" in license.upper():
      print("- ⬅️ Copyleft licensed tool found:", package['name'], "with license:", license)

    # Write to CSV
    with open(GITHUB_ORG+"_repo_dependency_licensing.csv", 'a', newline='') as file:
      # Initialize writer
      writer = csv.writer(file)
      
      # Write data
      field = [GITHUB_ORG, repo, package['name'], license]
      writer.writerow(field)


###
## Actually do stuff
###

# Check to make sure initial vars are present
if initial_var_validation() == True:
  GITHUB_ORG = os.environ['GITHUB_ORG']
  GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

# Build headers
headers = build_headers()

# Check rate limit
hold_until_rate_limit_success()

# Get all repo information
repo_names = get_all_repo_names()

# Initialize CSV
initialize_csv()

# Get dependencies for each repo, write to CSV
repo_count = len(repo_names)
index=1
for repo in repo_names:
  dependencies = get_repo_dependencies(repo, index, repo_count)
  index+=1
  
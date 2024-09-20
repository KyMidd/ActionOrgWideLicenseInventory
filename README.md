# ActionOrgWideLicenseInventory

## Summary

This tool is intended to be run in the context of a GitHub Organization. It uses a provided GitHub PAT and Organization name to iterate over every Repository within the Org, and download their dependencies and associated licenses. 

It stores all of that data in a single CSV that is returned as an artifact after the run. The artifact is a ZIP file called "org-license-csv", and when unzipped, it contains a single file called: "(org name)_repo_dependency_licensing.csv". 

This CSV file can be ready by automated tooling or simply with Excel/Google Sheets. 

## Why do we care about dependency licenses?

Of particular interest should be any licenses that are CopyLeft licenses. If you are selling/licensing your software, you shouldn't be packaging these tools with your software, because they aren't permitted to be sold in any way. More on Copyleft licenses here: https://en.wikipedia.org/wiki/Copyleft

## How does this work? 

This relies on a ton of great work that GitHub has already done as part of their SBOM (Software Bill of Materials) tooling. It discovers dependencies via most package manager files in each repo to discover the dependencies, and then works to classify the licenses of each one. That data is returned as part of the SBOM REST API, more info here: https://docs.github.com/en/rest/dependency-graph/sboms?apiVersion=2022-11-28

## Example action call

```yml
# This github action is used to inventory the license of every Repository within a GitHub Org
name: Org-Wide License Inventory
on: 
  workflow_dispatch:
    inputs:
      org_name:
        description: 'The name of the org to analyze'
        required: true
        type: string
  # Run nightly at 4a UTC / 10p CT
  schedule:
    - cron: "0 4 * * *"

jobs:
  license_analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: kymidd/ActionOrgWideLicenseInventory@v1
        with:
          GITHUB_ORG_NAME: your-org-name
          GITHUB_TOKEN: ${{ secrets.YOUR_GITHUB_PAT }}
```

## What permissions does the PAT require

The PAT (Personal Access Token) needs to have org:read as well as all repo:read permissions. org:read is used to list all the Repositories in the Org, and repo:read is used to read the SBOM REST API endpoint for each Repo. 

## Limitations

* Can't yet pass multiple Orgs, though I'd love to add that functionality as some point. 
* Must be run from a linux-based builder with `cp`, `python3`, and `pip`/`pip3`. 

## License

This tool is published under the MIT license. It can be used for any purpose, but carries no warranty, implied or otherwise. 
---
name: 🐛 Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''

---

<!--- Verify first that your issue is not already reported on GitHub -->
<!--- Also test if the latest release and devel branch are affected too -->

# Summary
<!--- Explain the problem briefly below -->

# Affected XLED components
<!--- Mark [x] for components that are affected -->

- [ ] Command Line Interface (CLI)
- [ ] Libary
- [ ] Documentation
- [ ] Other

# XLED version
<!--- If you have installed XLED from PyPI provide version from `pip show -V xled` -->
<!--- If you use git checkout provide output from `git describe` -->

# Twinkly device details
<!--- Project support only some device models. Provide details by calling its API where HOSTNAME is either IP address or host name of your device. -->

## Device information
<!--- Navigate to http://HOSTNAME/xled/v1/gestalt and pretty format output you get. Use e.g. http://jsonprettyprint.net/ . You can anonymize following fields: `hw_id`, `mac`, `uuid` by replacing some of the values, e.g. by "X"s . Paste output between quotes below: -->
```json
```
## Firmware version
<!--- Navigate to http://HOSTNAME/xled/v1/fw/version and pretty format output you get. Use e.g. http://jsonprettyprint.net/ . Paste output between quotes below: -->
```json
```
# Operating system
<!--- What operating system do you use? You can provide distribution and version as well -->

# Python version
<!--- Run `python --version` and paste output here. -->

# Steps to reproduce
<!--- Describe exactly how to reproduce the problem. E.g.: -->
<!--- 1. Run ... -->
<!--- 2. Or call ... -->
<!--- 3. See error -->

# Expected behavior
<!--- Describe what you expected to happen when running the steps above -->

# Actual results
<!--- Describe what actually happened. If you use CLI, use DEBUG level for all `--verbosity-*` options. -->

# Additional information
<!--- Anything else you would like to add? -->

# Python Server Plan

### Components
- [x] create data strucutres for the password and secrets data
- [x] create way to initialize those
- [ ] make function for of the type:
  - [ ] input username pass
  - [ ] return webpage they should see (login, bad, good + secrets)
- [x] helper function to look up secret for successful login
- [x] helper function to generate cookie on login
  - [x] then send the cookie to the user and make sure they set it
  - [ ] save the cookie locally so we remember it
    - [ ] cookie not found in table (login error)
    - [ ] not cookie (normal login w credentials)
- [ ] clear cookie functionality

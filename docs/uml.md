# UML Diagrams

## Class Diagram
+-------------------+        +-------------------+
|       User        |        |    Repository     |
+-------------------+        +-------------------+
| - id: String      |        | - id: String      |
| - username: String|        | - name: String    |
| - email: String   |        | - description: String|
+-------------------+        | - language: String|
| + getStarredRepos()|       | - starCount: Int  |
+-------------------+        +-------------------+
          ^                           ^
          |                           |
          |                           |
+-------------------+        +-------------------+
|   StarNetwork     |        | DiscoveredRepo    |
+-------------------+        +-------------------+
| - user: User      |        | - repo: Repository|
| - starredRepos: []|        | - mutualStars: Int|
+-------------------+        +-------------------+
| + discoverRepos() |        | + star()          |
| + generateDigest()|        | + ignore()        |
+-------------------+        +-------------------+


## Sequence Diagram

User            AuthService         GitHubAPI         DiscoveryService    EmailService
 |                   |                   |                   |                   |
 |  login            |                   |                   |                   |
 |------------------>|                   |                   |                   |
 |                   |  authenticate     |                   |                   |
 |                   |------------------>|                   |                   |
 |                   |     token         |                   |                   |
 |                   |<------------------|                   |                   |
 |  authenticated    |                   |                   |                   |
 |<------------------|                   |                   |                   |
 |                   |                   |                   |                   |
 |  getDiscoveredRepos                   |                   |                   |
 |-------------------------------------->|                   |                   |
 |                   |                   | fetchStarredRepos |                   |
 |                   |                   |<------------------|                   |
 |                   |                   |     repoData      |                   |
 |                   |                   |------------------>|                   |
 |                   |                   |                   | processData       |
 |                   |                   |                   |------------------>|
 |                   |                   |                   | discoveredRepos   |
 |                   |                   |                   |<------------------|
 |  discoveredRepos  |                   |                   |                   |
 |<--------------------------------------|                   |                   |
 |                   |                   |                   |                   |
 |                   |                   |                   | generateDigest    |
 |                   |                   |                   |------------------>|
 |                   |                   |                   |                   | sendEmail
 |                   |                   |                   |                   |---------->
# Obtaining an OAuth Client ID 

1. Visit the [Google API Console's Credentials Page](https://console.cloud.google.com/apis/credentials?project=youtube-api-468200)

2. Click `CREATE CREDENTIALS`, then `OAUTH CLIENT ID`

3. Click `CONFIGURE CONSENT SCREEN`

4. Select `EXTERNAL` and click `CREATE`

5. Name the application and click `SAVE`

6. Navigate to the credentials page again and click `CREATE CREDENTIALS`, then `OAUTH CLIENT ID`

7. Select `WEB APPLICATION` as the application type and `https://localhost:800/` under URIs

8. Click `CREATE`

9. Download the created client ID (button on the right)

10. Save the file as `client_secrets.json` and move it to the same directory as the program
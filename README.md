# Events-Booking-System
For my NEA, from September 2021 to March 2022, I was tasked with creating a fully functional booking system for a local events company. 
The purpose of the project was to automate the booking process, because the client was struggling to organise their bookings, correctly charge customers, and ensure attendants were fairly chosen for the event in question.
The program is written solely in Python and SQL.
A simplistic user interface was requested by the client, which was created using the TKinter library.
For security reasons, the database containing all the user information was not added to the raspatory, as it would be a breach of user data.

# Features Implemented

Password hashing was a key feature of the program. Hash ```sha256``` with 310000 iterations was used to improve the security of the database, ensuring if the database was breached, then all user passwords were hashed securely. A salt was also added to the hash to greatly improve the security. The salt consisted of a 32 length string of random digits, generated from the operating system.

A verification process was implemented, in which users would need to authenticate their login attempt. This was done by a random 6 digit code being emailed to the email address the user entered. If the code entered matched the one generated, they would be granted access. However, if invalid, they would not be given access to the system.  
![image](https://github.com/Danielx2003/Events-Booking-System/assets/70431670/fa4b7f9d-bc98-4438-a798-80d84c71a07d)  
The above image is an example of the email a user would receive containing their code.  

Details of the booking, including price, location and date would be emailed to the client and the attendant selected. This was to ensure that both parties were aware of the booking and could adequately prepare for the event.  
![image](https://github.com/Danielx2003/Events-Booking-System/assets/70431670/47bc9743-e563-4629-901c-5b38adea1bc7)
  
The above image shows an example of an email received after a successful booking was made.

The price of the booking was calculated based on many factors, including; distance to the venue, length of hire, prints per booth use, days till hire and more.
The distance to venue was calculate by making requests to the Google Maps API, using the distance matrix feature.
This feature takes 2 main arguments, being the addresses of the start location and the end location. This request then returned the distance, in miles, to the destination. 

Levenstein edit distance was used for string similarity matching to reduce the clutter within the database, thus making the program more efficient. __
This worked using Matrices. __
![image](https://github.com/Danielx2003/Events-Booking-System/assets/70431670/293a0710-f4d3-45d1-9b5c-4986ef7eec7f)
__

In this matrix, we can see the edit distance would have been 1, as there is 1 letter difference between the words ```hem``` and ```hey```.
This feature was used for user addresses, attempting to catch any spelling mistakes make, e.g. __Longbrok Road__ rather than __Longbrook Road__. It is clear these addresses are the same, as their postcodes would match, but the name just different. 
To ensure that the name entered was a mistake, and did match that of one within the database, a 70% similarity was chosen. 

SQL was a massive feature of this program, with many calls made, such as aggregate calls.

  
![image](https://github.com/Danielx2003/Events-Booking-System/assets/70431670/9a315deb-e8a8-432a-9649-791bec22540f)
  
Clear and concise alert messages were implemented to help the user fix any issues they may have encountered.
Error handling was vital for this project, as if the program crashed, all user data that had not been inputted into the database would have been lost.

# Functional Requirements – Bilticket Theatre Ticket Selling System

These requirements outline the expected behaviour for customers, admins, and theatre officers using the Bilticket platform.

## Customer Experience

1. **Account creation and login**
   - Sign up with email, password, first name, and last name.
   - Log in using the created credentials.

2. **Profile management**
   - Update address, phone number, and credit card information from the customer profile.
   - Bookings require valid credit card information; without it, customers cannot book seats.

3. **Searching plays**
   - Access the **Search Plays** page to view all plays.
   - Filter plays by title, genre, or playwright.

4. **Viewing stagings**
   - Selecting a play shows its stagings, each displaying date, theatre name, and the total number of empty seats.
   - Selecting a staging reveals theatre details and every available empty seat.

5. **Booking seats**
   - Choose at least two different empty seats for a staging and book them.
   - Successful booking reduces the number of empty seats accordingly.

6. **Reviewing bookings**
   - From the profile page, view all bookings along with their theatre, play, and staging information.

7. **Commenting on attended stagings**
   - View plays previously attended, then select a play to list only the stagings the customer attended.
   - For any attended staging without a comment, submit a new comment.
   - Comments display the staging attended, comment date, and a censored version of the customer’s name.
   - Comments are visible to other customers on the play’s page.

## Admin Experience

1. **Play creation**
   - Log in as an admin and create a new play by entering all play details.
   - Within the creation flow, display all artists with their details and select those performing in the play.

2. **Assigning stagings**
   - Display all theatres and select those that will stage the new play.
   - Create at least two stagings for the new play.
   - Ensure new stagings do not overlap with existing stagings in the same theatre.
   - Confirm changes to persist the play, artist associations, and stagings.

3. **Managing existing plays**
   - Display all plays and their details.
   - Select the newly created play, choose a staging, and edit its details.
   - After updates, log out so customers can view the changes.

## Theatre Officer Experience

1. **Viewing and filtering stagings**
   - Log in as a theatre officer to see all upcoming stagings in the assigned theatre.
   - Filter stagings by date and time.

2. **Staging details**
   - Select the closest staging to view the play, customers, and their booked seats.
   - Select a customer to see their name and contact information.

3. **Customer-facing confirmation**
   - After logging out, customers should be able to see the newly created plays and stagings, including artist lists and staging details.
   - Customer comments added to attended stagings must remain visible with censored names and staging references.


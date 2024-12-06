import requests
from bs4 import BeautifulSoup
import re
import os
from app3 import sendSMS

def fetch_results(registration_number):
    # URL of the results page
    base_url = "http://www.srkrexams.in/Login.aspx"
    results_url = "http://www.srkrexams.in/Result.aspx"

    try:
        # Create a session to maintain cookies
        session = requests.Session()

        # Step 1: Get the initial page to extract VIEWSTATE and EVENTVALIDATION
        response = session.get(base_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
        eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']

        # Step 2: Simulate the __doPostBack call to navigate to the results section
        post_data = {
            '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$lnkResult',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate,
            '__EVENTVALIDATION': eventvalidation
        }
        result_response = session.post(base_url, data=post_data)
        result_response.raise_for_status()

        # Parse the results section for the specific result link
        result_soup = BeautifulSoup(result_response.text, 'html.parser')
        result_link = result_soup.find('a', string=re.compile(r'(?=.*r20)(?=.*iv)(?=.*regular)(?=.*nov)(?=.*2024)', re.IGNORECASE))

        if not result_link:
            return {"error": "Result link not found"}
        sendSMS("4 1 results declared")
        # Extract the EVENTTARGET for the result
        href_value = result_link['href']
        event_target = href_value.split("'")[1]

        # Update form data to access specific result
        viewstate = result_soup.find('input', {'name': '__VIEWSTATE'})['value']
        eventvalidation = result_soup.find('input', {'name': '__EVENTVALIDATION'})['value']

        post_data = {
            '__EVENTTARGET': event_target,
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate,
            '__EVENTVALIDATION': eventvalidation
        }

        specific_result_response = session.post(base_url, data=post_data)
        specific_result_response.raise_for_status()

        # Final step: Submit registration number to fetch results
        specific_result_soup = BeautifulSoup(specific_result_response.text, 'html.parser')
        viewstate = specific_result_soup.find('input', {'name': '__VIEWSTATE'})['value']
        eventvalidation = specific_result_soup.find('input', {'name': '__EVENTVALIDATION'})['value']

        post_data = {
            '__VIEWSTATE': viewstate,
            '__EVENTVALIDATION': eventvalidation,
            'ctl00$ContentPlaceHolder1$txtRegNo': registration_number,
            'ctl00$ContentPlaceHolder1$btnGetResult': 'Get Result'
        }

        final_response = session.post(results_url, data=post_data)
        final_response.raise_for_status()

        soup = BeautifulSoup(final_response.text, 'html.parser')
        results_dict = {}

        # Extract student name
        try:
            name_input = soup.find('input', {'id': 'ContentPlaceHolder1_txtStudentName'})
            results_dict['name'] = name_input['value'] if name_input else 'Name not found'
        except Exception:
            results_dict['name'] = 'Error fetching name'

        # Extract SGPA
        try:
            sgpa_span = soup.find('span', {'id': 'ContentPlaceHolder1_gvSGPA_CGPA_lblSgap_0'})
            results_dict["SGPA"] = sgpa_span.get_text(strip=True) if sgpa_span else 'SGPA not found'
        except Exception:
            results_dict["SGPA"] = 'Error fetching SGPA'

        # Extract CGPA
        try:
            cgpa_span = soup.find('span', {'id': 'ContentPlaceHolder1_gvSGPA_CGPA_lblCGPA_0'})
            results_dict["CGPA"] = cgpa_span.get_text(strip=True) if cgpa_span else 'CGPA not found'
        except Exception:
            results_dict["CGPA"] = 'Error fetching CGPA'

        # Extract subject grades
        try:
            table = soup.find('table', {'id': 'ContentPlaceHolder1_dgvStudentHistory'})
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 4:
                    subject_name = cells[1].get_text(strip=True)
                    grade = cells[3].get_text(strip=True)
                    results_dict[subject_name] = grade
        except Exception:
            results_dict["Subjects"] = "Error fetching subject grades"
        sendSMS(str(results_dict))
        return results_dict

    except requests.exceptions.RequestException as e:
        return {"error": f"HTTP error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# Use environment variable for registration number
registration_number = os.environ.get('REG_NUMBER')
print(registration_number)
result = fetch_results(registration_number)
print(result)

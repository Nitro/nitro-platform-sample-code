# Test Files for Employee Policy Distribution

This folder contains test data for the `send_policies_to_employees.py` script.

## Contents

### Policy Documents
- `company-policies.pdf` - Sample company policy document
- `confidentiality-agreement.pdf` - Sample confidentiality agreement

### Employee Data
- `employees.csv` - List of 3 test employees with name and email

## Usage

### From the samples/python directory:

```bash
# Run the script with these test files
python send_policies_to_employees.py \
  ../../test_files/test-sign \
  ../../test_files/test-sign/employees.csv \
  ./output/test-sign-output

# Or use separate policies folder and CSV
python send_policies_to_employees.py \
  ../../test_files/test-sign \
  ../../test_files/test-sign/employees.csv \
  ./output/newJoinersJanuary
```

### Expected Output Structure

```
output/test-sign-output/
├── john-doe/
│   ├── signed-policies.pdf
│   ├── envelope-info.json
│   └── envelope-id.txt
├── jane-smith/
│   ├── signed-policies.pdf
│   ├── envelope-info.json
│   └── envelope-id.txt
└── bob-johnson/
    ├── signed-policies.pdf
    ├── envelope-info.json
    └── envelope-id.txt
```

## Notes

- **Important**: Update the email addresses in `employees.csv` to real email addresses you can access before testing
- The script will send signature requests to these emails
- You'll need to sign the documents to complete the test
- For testing without waiting, add `--no-wait` flag

## Test Workflow

1. Update emails in `employees.csv` to your test email addresses
2. Run the script with the command above
3. Check your email for signature requests
4. Sign the documents through the email link
5. Script will download signed PDFs to output folders

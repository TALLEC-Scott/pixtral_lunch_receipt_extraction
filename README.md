# Automating Receipt Entry with Mistral's Pixtral

Having a bit of fun with Mistral's Pixtral model via API for VQA (Visual Question and Answering) to automate my weekly task of entering my lunch receipts into my company's system which takes me roughly 10-15 minutes every week.

## Objective

Here's how it works:

1. **Receipt Capture**:  
   Scan a receipt or take a picture of it on your phone and then send to my work email.
2. **Automatic Processing**:  
   Once the mail with the image attached is received, the system automatically:
   - Extracts key information from the receipt, in my case (total price, date).
   - Transcribes this information into a structured format (json).  
3. **Integration**:  
   //TODO The extracted data is sent through the appropriate processes in the company's system for further handling.


## Example 

```json {
  "total_price": "5.08",
  "date": "23-04-2012"
}```

![lunch_receipt_04_23_2012](https://github.com/user-attachments/assets/6bf85e4d-8b66-4baa-801f-541085c78de1)

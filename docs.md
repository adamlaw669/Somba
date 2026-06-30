> ## Documentation Index
> Fetch the complete documentation index at: https://developer.nomba.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Virtual accounts

> Learn about creating virtual accounts

<CardGroup cols={2}>
  <Card title="Create a virtual account" icon="cart-shopping" href="/nomba-api-reference/virtual-accounts/create-virtual-account">
    Generate a unique account number for your customer to receive payment.
  </Card>

  <Card title="Update a virtual account" icon="pen-to-square" href="/nomba-api-reference/virtual-accounts/update-a-virtual-account">
    Update a customer virtual account name and callback URL record.
  </Card>
</CardGroup>

## Introduction

At Nomba, virtual accounts are part of the broader Accounts system. A virtual account can be created for a customer primarily to receive payments.
Once created, Nomba generates a unique account number that customers can use to receive bank transfers.

### Types of accounts

Nomba supports the following account types:

#### Primary Accounts

A primary account is automatically created when you set up your business on Nomba.

* This is your main account.
* All other accounts (virtual or sub-accounts) are linked to it.

#### Virtual accounts

Virtual accounts are created via API for receiving payments.
Funds received are automatically routed to the parent (primary) account.

* Virtual accounts do not hold balances themselves
* If required, virtual accounts can be linked to a sub-account instead of the primary account buy adding the `subAccountId` as a path to the [endpoint](/nomba-api-reference/virtual-accounts/create-virtual-account-for-sub-account)
* You can view all virtual account transactions on your dashboard.

#### Sub-accounts

Sub-accounts are created from the Nomba Dashboard

* They act as separate “pockets” for managing funds
* Useful for segmenting funds across teams, operations, or workflows.

See this [guide](/docs/guides/managing-accounts-with-nomba) for more details on managing accounts with Nomba.

### Types of Virtual accounts

Nomba supports two types of virtual accounts based on their behavior:

#### Static Virtual Accounts

Static virtual accounts are permanent account numbers assigned to a customer or business.

Use a static virtual account when:

* You do not want the account to expire
* You want your customers to receive multiple payments over time.

**Use cases:**

* Assigning a dedicated account number to a customer
* Supporting recurring payments
* When you need a stable, non-expiring account number

#### Dynamic Virtual Accounts

Dynamic virtual accounts are temporary, purpose-specific account numbers.

* Typically used for one-time or time-bound payments
* Can be configured with an `expiryDate` to define validity
* Dynamic accounts help reduce reconciliation errors for transaction-specific payments.

## Create a virtual account

We recommend testing virtual account creation in the Sandbox environment before going live.

<Note>
  * Each user can create a maximum of **2 virtual accounts**
  * Each account can receive transfers up to ₦150
  * Transfers can be made from any Nigerian bank.
  * You can update the expected amount (up to ₦150) using the `expectedAmount` field.
</Note>

* All transfers will trigger webhooks to the Sandbox webhook URL.
* Virtual account expiration is not supported in Sandbox.

To create a virtual account, please take note of the optional and required fields:

* `accountRef` (required): A unique reference you assign to the virtual account.

* `accountName` (required): The name associated with the virtual account.

* `currency` (required): Currency for the virtual account, e.g NGN.

* `bvn` (optional): If not provided, the virtual account will inherit the BVN of the parent account. Only include this if you want to assign a different BVN.

* `expectedAmount` (optional): Restricts the account to accept only the specified amount. This is useful for exact payments such as invoice matching or controlled transfers.  When omitted, the account will accept any amount since it is not restricted to a specific value.

If a sender transfers an amount different from the expectedAmount:

* The transaction may be declined by the sender’s bank, or
* Automatically reversed, depending on the bank’s handling logic

<Warning>
  Be cautious when setting the `expectedAmount`. Once set, the account will **only** accept that exact amount. Payments with any other amount will be rejected.
</Warning>

* `expiryDate` (optional): Sets how long the virtual account remains valid, this is useful if you intend to create a dynamic virtual account purposely for time-based transactions. If omitted, the virtual account functions as a static (permanent) account.

To create a virtual account, send a [POST request](/nomba-api-reference/virtual-accounts/create-virtual-account) to this endpoint `/v1/accounts/virtual`.

<CodeGroup>
  ```bash Request theme={null}
  curl --request POST \
    --url https://api.nomba.com/v1/accounts/virtual \
    --header 'Authorization: Bearer <token>' \
    --header 'Content-Type: application/json' \
    --header 'accountId: <parent accountId>' \
    --data '{
      "accountRef": "1oWbJQQHLyQ************",
      "accountName": "Daniel Scorsese",
      "currency": "NGN",
      "expiryDate": "2024-06-17 04:55:00",
      "bvn":"12345678901",
      "expectedAmount": 5000.00,
    }'
  ```

  ```json Response theme={null}
  {
    "code": "00",
    "description": "Success",
    "data": {
      "createdAt": "2024-10-11T14:15:39.376Z",
      "accountRef": "1oWbJQQHLyQqqf1SwxjSpudeA2q3",
      "accountHolderId": "8d19d421-85b1-4b61-be90-168dc261gf45",
      "accountName": "Femi-Testing",
      "currency": "NGN",
      "bankAccountNumber": "91714245345",
      "bankAccountName": "Femi-Testing/Testing mike",
      "bankName": "Amucha MFB",
      "bvn": "22122204392",
      "expiryDate": "2024-10-12T12:30:49",
      "expired": false
    }
  }
  ```
</CodeGroup>

## Suspend a virtual account

You cannot suspend a parent account. The parent account is directly tied to your business and always remains active. Only accounts created via the API (i.e., virtual accounts) can be suspended.

To suspend a virtual account, send a PUT request with the accountId of the account you want to suspend to `/v1/accounts/suspend/{accountId}`

<Info>
  Virtual accounts are the only accounts that can be created via API.
</Info>

<CodeGroup>
  ```bash Request theme={null}
  curl --request PUT \
    --url https://api.nomba.com/v1/accounts/suspend/{accountId} \
    --header 'Authorization: Bearer <token>' \
    --header 'accountId: <accountid>'
  ```

  ```bash Response theme={null}
  {
    "code": "00",
    "description": "Success",
    "data": true
  }
  ```
</CodeGroup>

## Perform a virtual account lookup

You can look up the details of a virtual account using its account number. This is useful for verifying whether an account is still valid, checking expiry status, or retrieving account details before accepting payments.

<CodeGroup>
  ```bash Request theme={null}
  curl --request GET \
    --url https://api.nomba.com/v1/accounts/virtual/{virtualAcctNumber} \
    --header 'Authorization: Bearer <token>' \
    --header 'accountId: <accountId>'
  ```

  ```json Response theme={null}
  {
      "code": "00",
      "description": "SUCCESS",
      "data": {
          "createdAt": "2025-05-28T08:23:48.073Z",
          "bankAccountNumber": "",
          "bankAccountName": "",
          "bankName": "Nombank MFB",
          "accountRef": "created-wed-28-05-2501",
          "accountHolderId": "",
          "accountName": "",
          "currency": "NGN",
          "bvn": "00***",
          "expired": false
      },
      "message": "SUCCESS",
      "status": true
  }
  ```
</CodeGroup>

**What’s Next?**

After creating a virtual account, there are additional actions you may need to perform:

* [Expire a virtual account](/nomba-api-reference/virtual-accounts/expire-a-virtual-account) Set a virtual account to expire at a specific time.

* [Filter virtual accounts](/nomba-api-reference/virtual-accounts/filter-virtual-accounts) Retrieve a list of accounts that match specific conditions (e g, expired, by customer account name etc).

* [Fetch parent account balance](/nomba-api-reference/accounts/fetch-parent-account-details).


> ## Documentation Index
> Fetch the complete documentation index at: https://developer.nomba.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Verify Transactions

> Learn how to verify checkout transactions using the Nomba API

<CardGroup cols={2}>
  <Card title="Verify by Order Reference" icon="magnifying-glass" href="/nomba-api-reference/transactions/filter-parent-account-transactions">
    Look up a transaction using your order reference or the Nomba transaction ID.
  </Card>

  <Card title="Fetch Checkout Transaction (Production)" icon="file-invoice-dollar" href="/nomba-api-reference/online-checkout/fetch-checkout-transaction">
    Retrieve full checkout order details including card and transfer info.
  </Card>
</CardGroup>

## Which endpoint should I use?

There are two ways to verify a checkout transaction. Choose based on your environment and what you need:

| Endpoint                           | Method | Environment          | Use when                                                                                                                              |
| ---------------------------------- | ------ | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `/v1/transactions/accounts/single` | GET    | Sandbox + Production | You want to confirm `status: SUCCESS` before delivering value. Works with both `orderReference` and `transactionRef` as query params. |
| `/v1/checkout/transaction`         | GET    | **Production only**  | You need full checkout order details (card info, transfer details, order metadata).                                                   |

<Tip>
  Always verify transactions before providing goods or services to your customer — even if you received a webhook.
</Tip>

## Option 1: Verify via `/v1/transactions/accounts/single`

This endpoint works in both sandbox and production. Pass the `orderReference` (the reference on the order) or the `transactionRef` (the Nomba transaction ID from the webhook) as a query parameter.

The key field to check in the response is `data.status`. A successful payment returns `"status": "SUCCESS"`.

<CodeGroup>
  ```bash Verify by orderReference theme={null}
    curl --request GET \
      --url 'https://api.nomba.com/v1/transactions/accounts/single?orderReference=90e81e8a-bc14-4ebf-89c0-57da801cca68' \
      --header 'Authorization: Bearer <token>' \
      --header 'accountId: <accountid>'
  ```

  ```bash Verify by transactionRef theme={null}
    curl --request GET \
      --url 'https://api.nomba.com/v1/transactions/accounts/single?transactionRef=WEB-ONLINE_C-69923-ae0f2688-12b1-45b6-9972-06261aa65ef1' \
      --header 'Authorization: Bearer <token>' \
      --header 'accountId: <accountid>'
  ```

  ```javascript Node.js theme={null}
  // Verify by orderReference
  const orderReference = '90e81e8a-bc14-4ebf-89c0-57da801cca68';
  const url = new URL('https://api.nomba.com/v1/transactions/accounts/single');
  url.searchParams.set('orderReference', orderReference);

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'accountId': accountId,
    },
  });

  const { code, data } = await response.json();
  if (code !== '00') throw new Error('Transaction not found');

  if (data.status === 'SUCCESS') {
    // Payment confirmed — deliver goods/services
  }
  ```

  ```python Python theme={null}
  import requests

  order_reference = '90e81e8a-bc14-4ebf-89c0-57da801cca68'

  response = requests.get(
      'https://api.nomba.com/v1/transactions/accounts/single',
      headers={
          'Authorization': f'Bearer {access_token}',
          'accountId': account_id,
      },
      params={'orderReference': order_reference},
  )

  result = response.json()
  if result['code'] != '00':
      raise Exception('Transaction not found')

  if result['data']['status'] == 'SUCCESS':
      pass  # Payment confirmed — deliver goods/services
  ```

  ```json expandable Response (Success) theme={null}
  {
    "code": "00",
    "description": "SUCCESS",
    "data": {
        "id": "WEB-ONLINE_C-69923-ae0f2688-12b1-45b6-9972-06261aa65ef1",
        "status": "SUCCESS",
        "amount": "202.8",
        "fixedCharge": "2.8",
        "source": "web",
        "type": "online_checkout",
        "gatewayMessage": "PAYMENT SUCCESSFUL",
        "customerBillerId": "7373019705",
        "timeCreated": "2025-09-26T01:07:02.729Z",
        "timeUpdated": "2025-09-26T01:07:02.989Z",
        "walletCurrency": "NGN",
        "walletBalance": "478.97",
        "billingVendorReference": "68d5e736e414b032b3******",
        "paymentVendorReference": "09064525092601065923059812******",
        "userId": "69923f4d-963f-4a2b-b0f5-4da074d0a461",
        "onlineCheckoutOrderId": "9adcbf44-8cca-4fc6-b3a7-ac2758******",
        "onlineCheckoutOrderReference": "90e81e8a-bc14-4ebf-89c0-57da801c******",
        "onlineCheckoutCurrency": "NGN",
        "onlineCheckoutCustomerEmail": "make@gmail.com",
        "currency": "NGN",
        "onlineCheckoutAmount": "202.8",
        "onlineCheckoutPaymentMethod": "bank_transfer",
        "entryType": "CREDIT"
    }
  }
  ```

  ```json Response (Failed / Not Found) theme={null}
  {
    "code": "01",
    "description": "Transaction not found",
    "data": null
  }
  ```
</CodeGroup>

<Note>
  For sandbox transactions, use the sandbox base URL: `https://sandbox.nomba.com/v1/transactions/accounts/single`. See [Sandbox Testing](/docs/products/accept-payment/sandbox-testing) for details on looking up sandbox transactions.
</Note>

## Option 2: Get Checkout Transaction (Production only)

This endpoint returns full checkout order details including card information, transfer details, and order metadata. It is useful when you need richer data than the basic transaction lookup provides — for example, to display order details on a receipt page.

<Warning>
  This endpoint is only available in the **production** environment. For sandbox verification, use `POST /v1/transactions/accounts` with the transaction reference — see [Sandbox Testing](/docs/products/accept-payment/sandbox-testing).
</Warning>

To fetch a checkout transaction, send a [GET request](/nomba-api-reference/online-checkout/fetch-checkout-transaction) to this endpoint `/v1/checkout/transaction`.

<CodeGroup>
  ```bash Request theme={null}
    curl --request GET \
      --url 'https://api.nomba.com/v1/checkout/transaction?idType=ORDER_REFERENCE&id=68da39e0-2ce4-4ea6-9def-5*********' \
      --header 'Authorization: Bearer <token>' \
      --header 'accountId: <accountid>'
  ```

  ```json Response theme={null}
    {
      "code": "00",
      "description": "Success",
      "data": {
        "success": "true",
        "message": "success",
        "order": {
          "orderId": "56e03654-0c32-4d3e-bbd6-a9df22994a12",
          "orderReference": "90e81e8a-bc14-4ebf-89c0-57da752cca58",
          "customerId": "762878332454",
          "accountId": "56e03654-0c32-4d3e-bbd6-a9df22994a12",
          "callbackUrl": "https://ip:port/merchant.com/callback",
          "customerEmail": "abcde@gmail.com",
          "amount": "10000.00",
          "currency": "NGN"
        },
        "transactionDetails": {
          "transactionDate": "2023-12-06T15:46:43.000Z",
          "paymentReference": "5844858382134",
          "paymentVendorReference": "5844858382675493",
          "tokenizedCardPayment": "true",
          "statusCode": "Payment approved"
        },
        "transferDetails": {
          "sessionId": "67584432178569543",
          "beneficiaryAccountName": "Tope Fade",
          "beneficiaryAccountNumber": "5844858382",
          "originatorAccountName": "Femi Fash",
          "originatorAccountNumber": "3409082834",
          "narration": "Checkout payment",
          "destinationInstitutionCode": "true",
          "paymentReference": "44384586756"
        },
        "cardDetails": {
          "cardPan": "515123 **** **** 6667",
          "cardType": "Verve",
          "cardCurrency": "NGN",
          "cardBank": "057"
        }
      }
    }
  ```
</CodeGroup>



> ## Documentation Index
> Fetch the complete documentation index at: https://developer.nomba.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Fetch Transactions

> Learn how to fetch transactions associated with an account.

<CardGroup cols={2}>
  <Card title="Fetch transactions on the parent account" icon="receipt" href="/nomba-api-reference/transactions/fetch-transactions-on-the-parent-account" />

  <Card title="Filter parent account transactions" icon="filter" href="/nomba-api-reference/transactions/filter-parent-account-transactions" />
</CardGroup>

## Overview

You may need to check the status of a transaction or retrieve a list of transactions for reconciliation purposes.

Nomba provides multiple APIs for fetching different types of transactions—for example, debit/credit, virtual account, or parent account transactions. Depending on your use case, you can explore the relevant fetch transaction endpoint.

<Note>
  Transaction APIs are paginated. We recommend reviewing the [pagination guide](/docs/api-basics/pagination) to understand how to work with paginated endpoints or trying out live API interactions to see how it works in practice.
</Note>

## Fetch Account Transactions

To fetch account transactions within a specific timeframe, make a [GET request](/nomba-api-reference/transactions/fetch-transactions-on-the-parent-account) to `/v1/transactions/accounts` or see the sample request and response below:You can pass a query param to specify a timeframe by passing `dateFrom` and `dateTo` as part of the request. You can also set a limit, as it's a paginated endpoint.

To learn how Nomba handles pagination, [check here.](/docs/api-basics/pagination)

<CodeGroup>
  ```bash Request theme={null}
  curl --request GET \
    --url https://api.nomba.com/v1/transactions/accounts?limit=10&dateFrom=2023-01-01T00%3A00%3A00&dateTo=2025-01-01T00%3A00%3A00'  \
    --header 'Authorization: Bearer <token>' \
    --header 'accountId: <accountId>'
  ```

  ```json expandable Response theme={null}
  {
    "code": "00",
    "description": "Success",
    "data": {
      "results": [
        {
          "id": "POS-WITHDRAW-DFC05-693cd007-cd1e-4ea6-8b79-5f5c4d7a83ea",
          "status": "SUCCESS",
          "amount": 4000,
          "fixedCharge": 123,
          "source": "pos",
          "type": "withdrawal",
          "gatewayMessage": "SUCCESS",
          "customerBillerId": "539983 **** **** 5118",
          "timeCreated": "2023-09-08T19:26:34.657000Z",
          "posTid": "2KUD4AKB",
          "terminalId": "2KUD4AKB",
          "providerTerminalId": "2KUD4AKB",
          "rrn": "230908202632",
          "posSerialNumber": "91230309116826",
          "posTerminalLabel": "KEB MUSA ABUBAKAR",
          "stan": "556734",
          "paymentVendorReference": "2KUD4AKB230908202632",
          "userId": "dfc05ca1-4e75-41dd-8e41-2d362d565893",
          "posRrn": "230908202632",
          "merchantTxRef": "c90d-4b25-ad0f"
        }
      ],
      "cursor": "xchbaVFsjdsbaADddd"
    }
  }
  ```
</CodeGroup>

## Fetch Bank Transactions

To fetch debit or credit transactions associated with an account, make a [GET Request](/nomba-api-reference/transactions/fetch-creditdebit-transactions-on-the-parent-account) to `/v1/transactions/bank`.

<CodeGroup>
  ```bash Request theme={null}
    curl --request GET \
      --url https://api.nomba.com/v1/transactions/bank \
      --header 'Authorization: Bearer <token>' \
      --header 'accountId: <accountId>'
  ```

  ```json expandable Response theme={null}
    {
      "code": "00",
      "description": "Success",
      "data": {
        "results": [
          {
            "amount": 7000,
            "currency": "NGN",
            "meta": {
              "billerId": "API_FCIR5UQFMYS",
              "terminalActionId": "",
              "productId": "p2p",
              "fee": 0,
              "type": "p2p",
              "transactionId": "API-P2P-84026-d8a4d658-6747-418d-a7e2-37bc6290310d",
              "rrn": "",
              "parentAccountId": "01a10aeb-d989-460a-bbde-9842f2b4320f",
              "terminalLabel": "",
              "accountId": "890022ce-bae0-45c1-9b9d-ee7872e6ca27",
              "merchantTxRef": "",
              "transactionAmount": 7000,
              "mCollectionsId": ""
            },
            "status": "SUCCESS",
            "timeUpdated": "2023-09-08T19:05:21.000Z",
            "walletBalance": 285951,
            "transactionType": "DEBIT"
          }
        ],
        "cursor": "xchbaVFsjdsbaADddd"
      }
    }
  ```
</CodeGroup>

## Fetch Virtual Account Transactions

To fetch transactions on a virtual account, make a GET request to `/v1/transactions/virtual`.

Pass the virtual\_account query parameter with the account number. You can also filter by `dateFrom` and `dateTo`.

<CodeGroup>
  ```bash Request theme={null}
  curl --request GET \
  --url'https://api.nomba.com/v1/transactions/virtual?virtual_account=8578228675&dateFrom=2025-06-24&dateTo=2025-06-25' \
  --header 'accountId: <your-account-id>' \
  --header 'Authorization: Bearer <your-token>'
  ```

  ```json expandable Response theme={null}
  {
      "code": "00",
      "description": "SUCCESS",
      "data": {
          "cursor": "",
          "results": [
              {
                  "id": "API-VACT_TRA-FFCBE-9eb634eb-4dc5-46a9-bb65-7d03d6b88c1c",
                  "status": "SUCCESS",
                  "amount": "100.0",
                  "fixedCharge": "0.5",
                  "source": "api",
                  "type": "vact_transfer",
                  "customerBillerId": "8065219824",
                  "timeCreated": "2025-06-24T11:31:35.017Z",
                  "timeUpdated": "2025-06-24T11:31:35.107Z",
                  "posTid": "",
                  "posSerialNumber": "",
                  "walletCurrency": "NGN",
                  "walletBalance": "457.0",
                  "billingVendorReference": "685a8c973ccb33995cbefc1f",
                  "paymentVendorReference": "038309078367093226893790137012",
                  "userId": "***",
                  "ktaSenderName": "John doe",
                  "ktaSenderAccountNumber": "8068952954",
                  "ktaSenderBankCode": "Paycom (Opay)",
                  "recipientAccountNumber": "8578228675",
                  "recipientAccountType": "VIRTUAL",
                  "senderName": "John Doe",
                  "currency": "NGN",
                  "bankCode": "305",
                  "productId": "305",
                  "isAgentTransaction": true,
                  "isInternational": false,
                  "customerCommission": "0.00",
                  "recipientAccountName": "Clean/Agboola Oyenike",
                  "sessionId": "100004250624113131135397696024",
                  "accountNumber": "8028952054",
                  "bankName": "Paycom (Opay)",
                  "entryType": "CREDIT",
                  "transactionCategory": "Income",
                  "narration": "Transfer from John Doe",
                  "receiptTerminalId": ""
              }
          ]
      },
      "status": false
  }
  ```
</CodeGroup>

## Transaction Requery

Use this endpoint to confirm the status of a transaction using its `sessionId`.
To obtain a session ID, first filter through virtual account transactions to locate the transaction you want to requery.

<CodeGroup>
  ```bash Request theme={null}
  curl --request GET \
    --url https://api.nomba.com/v1/transactions/requery/<sessionId> \
    --header 'Authorization: Bearer <token>' \
    --header 'accountId: <accountId>'
  ```

  ```json expandable Response theme={null}
  {
      "code": "00",
      "description": "Requery Successful",
      "data": {
          "id": "API-VACT_TRA-185C7-01964b64-5c0a-4c91-81b6-zxv7a421862b",
          "status": "SUCCESS",
          "amount": "200.0",
          "fixedCharge": "1.0",
          "source": "api",
          "type": "vact_transfer",
          "customerBillerId": "0122408496",
          "timeCreated": "2024-07-11T16:12:49.656Z",
          "walletBalance": "1648.79",
          "billingVendorReference": "029004810da38748e93ca4a9",
          "paymentVendorReference": "000132891359184717316165338085",
          "userId": "185c75d9-6ae0-675r-950e-425666184ed6",
          "ktaSenderName": "Smart Hamzat",
          "ktaSenderAccountNumber": "0122408496",
          "ktaSenderBankCode": "Amucha MFB (Nomba)",
          "recipientAccountNumber": "0014701211",
          "recipientAccountType": "VIRTUAL",
          "senderName": "Smart Hamzat",
          "bankCode": "090645",
          "productId": "090645",
          "isAgentTransaction": true,
          "isInternational": false,
          "customerCommission": 0,
          "recipientAccountName": "John Amazing Doe",
          "sessionId": "000132891359184717316165338085",
          "accountNumber": "0122408496",
          "bankName": "Amucha (Nomba)"
      }
  }
  ```
</CodeGroup>


> ## Documentation Index
> Fetch the complete documentation index at: https://developer.nomba.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Setting up webhooks

> Guidance on how to configure your webhooks on your Nomba dashboard.

Setting up your webhook through the Nomba dashboard is a straightforward process. Before configuring your webhooks, your dashboard will resemble the image below.

<Frame caption="Setting up your webhooks">
  <img src="https://mintcdn.com/nombainc/VJp6uGRaVI4ms-qk/images/setup-webhooks-1.png?fit=max&auto=format&n=VJp6uGRaVI4ms-qk&q=85&s=a2f6529ca30db31140766be28e494a42" style={{ borderRadius: '0.5rem' }} loading="lazy" width="1920" height="958" data-path="images/setup-webhooks-1.png" />
</Frame>

To initiate the setup, proceed by adding your webhook URL and the corresponding signature key. Additionally, carefully select the events you wish to monitor. For a comprehensive understanding of available webhook events, refer to the [Webhooks documentation](/docs/api-basics/webhook).

<Tip>
  Before inclusion, we perform a validation check on the webhook URL to ensure it is ready to accept HTTP RESTful POST calls. Please ensure your webhook URL is prepared for seamless integration.
</Tip>

<Frame caption="Select an event type">
  <img src="https://mintcdn.com/nombainc/Poj72ShpATL2Kn8l/images/setup-webhooks-2.png?fit=max&auto=format&n=Poj72ShpATL2Kn8l&q=85&s=1a8ddec158511df7945e72a3ae08bd33" style={{ borderRadius: '0.5rem' }} loading="lazy" width="2880" height="1782" data-path="images/setup-webhooks-2.png" />
</Frame>

<Tip>
  It's crucial to remember your Signature Key, as it plays a vital role in the signature verification process, especially when generating an HMAC signature.
</Tip>

Once you have successfully subscribed to events via your webhooks, your dashboard will reflect the configured events. Take care to subscribe to the appropriate events to tailor your webhook functionality to your specific needs.

<Frame caption="Setting up your webhooks">
  <img src="https://mintcdn.com/nombainc/Poj72ShpATL2Kn8l/images/setup-webhooks-3.png?fit=max&auto=format&n=Poj72ShpATL2Kn8l&q=85&s=c3d89f06db3d69e46dc20993c06d361d" style={{ borderRadius: '0.5rem' }} loading="lazy" width="2880" height="1782" data-path="images/setup-webhooks-3.png" />
</Frame>

Feel free to [Reach out](/support/reach-out) if you have any questions or need further assistance.


> ## Documentation Index
> Fetch the complete documentation index at: https://developer.nomba.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Authenticate

> Learn how to ensure secure access to Nomba API Resources.

## Overview

Nomba uses **OAuth 2.0** to secure API access.
You'll use your `client_id` and `client_secret` to obtain an `access_token`. To get the client credentials from the Nomba dashboard, follow the steps on how to [obtain API keys](/docs/getting-started/get-api-keys).

The authentication flow has three key steps:

1. **Obtain** an `access_token` and `refresh_token`
2. **Refresh** the token when it expires
3. **Revoke** the token when no longer needed

## Obtain Access Token

Use the `client_credentials` grant to request an `access_token` and `refresh_token`.  The `access_token` is required for making API requests.

<CodeGroup>
  ```bash cURL theme={null}
      curl --request POST \
        --url https://api.nomba.com/v1/auth/token/issue \
        --header 'Content-Type: application/json' \
        --header 'accountId: <accountid>' \
        --data '{
        "grant_type": "client_credentials",
        "client_id": "replace-with-your-client-id",
        "client_secret": "replace-with-your-client-secret"
      }'
  ```

  ```javascript Node.js theme={null}
  const response = await fetch('https://api.nomba.com/v1/auth/token/issue', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'accountId': '<accountid>',
    },
    body: JSON.stringify({
      grant_type: 'client_credentials',
      client_id: 'replace-with-your-client-id',
      client_secret: 'replace-with-your-client-secret',
    }),
  });

  const { code, data } = await response.json();
  if (code !== '00') throw new Error('Authentication failed');

  const { access_token, refresh_token, expiresAt } = data;
  ```

  ```python Python theme={null}
  import requests

  response = requests.post(
      'https://api.nomba.com/v1/auth/token/issue',
      headers={
          'Content-Type': 'application/json',
          'accountId': '<accountid>',
      },
      json={
          'grant_type': 'client_credentials',
          'client_id': 'replace-with-your-client-id',
          'client_secret': 'replace-with-your-client-secret',
      },
  )

  result = response.json()
  if result['code'] != '00':
      raise Exception('Authentication failed')

  access_token = result['data']['access_token']
  refresh_token = result['data']['refresh_token']
  ```

  ```json Response theme={null}
    {
      "code": "00",
      "description": "Success",
      "data": {
        "businessId": "01a10aeb-d989-460a-bbde-9842f2b4320f",
        "access_token": "eyJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "01h4gdx2tctxfjgacbdwrcvs5d1688473602892",
        "expiresAt": "2022-07-08T14:33:00Z"
      }
    }
  ```
</CodeGroup>

## Refresh Access Token

Access tokens expire after 30 minutes.
Instead of requesting a new token with your credentials, exchange the `refresh_token` for a new `access_token`.
This avoids exposing your client\_secret repeatedly and keeps the process secure.

<Note>
  We recommend refreshing your `access_token` at least 5 minutes before it expires.
</Note>

<CodeGroup>
  ```bash cURL theme={null}
    curl --request POST \
      --url https://api.nomba.com/v1/auth/token/refresh \
      --header 'Authorization: Bearer <token>' \
      --header 'Content-Type: application/json' \
      --header 'accountId: <accountid>' \
      --data '{
      "grant_type": "refresh_token",
      "refresh_token": "01h4gdx2tctxfjgacbdwrcvs5d1688473602892"
    }'
  ```

  ```javascript Node.js theme={null}
  const response = await fetch('https://api.nomba.com/v1/auth/token/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      'accountId': '<accountid>',
    },
    body: JSON.stringify({
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
    }),
  });

  const { code, data } = await response.json();
  if (code !== '00') throw new Error('Token refresh failed');

  const newAccessToken = data.access_token;
  ```

  ```python Python theme={null}
  import requests

  response = requests.post(
      'https://api.nomba.com/v1/auth/token/refresh',
      headers={
          'Authorization': f'Bearer {access_token}',
          'Content-Type': 'application/json',
          'accountId': '<accountid>',
      },
      json={
          'grant_type': 'refresh_token',
          'refresh_token': refresh_token,
      },
  )

  result = response.json()
  if result['code'] != '00':
      raise Exception('Token refresh failed')

  new_access_token = result['data']['access_token']
  ```

  ```json Response theme={null}
    {
      "code": "00",
      "description": "Success",
      "data": {
        "businessId": "01a10aeb-d989-460a-bbde-9842f2b4320f",
        "access_token": "eyJhbGciOiJIUzI1NiJ9...",
        "refresh_token": "01h4gdx2tctxfjgacbdwrcvs5d1688473602892",
        "expiresAt": "2022-07-08T14:33:00Z"
      }
    }
  ```
</CodeGroup>

## Revoke Access Token

Revoke an `access_token` when you need to immediately terminate access.
This is useful if the token is compromised, expired, or no longer needed.
Once revoked, the token is invalid and cannot be used to access resources.

<CodeGroup>
  ```bash cURL theme={null}
    curl --request POST \
      --url https://api.nomba.com/v1/auth/token/revoke \
      --header 'Content-Type: application/json' \
      --header 'accountId: <accountid>' \
      --data '{
      "clientId": "2242b79d-f2cf-4ccc-ada1-e890bd1a9f0d",
      "access_token": "<access_token_to_revoke>"
    }'
  ```

  ```javascript Node.js theme={null}
  const response = await fetch('https://api.nomba.com/v1/auth/token/revoke', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'accountId': '<accountid>',
    },
    body: JSON.stringify({
      clientId: '2242b79d-f2cf-4ccc-ada1-e890bd1a9f0d',
      access_token: accessToken,
    }),
  });

  const { code } = await response.json();
  if (code !== '00') throw new Error('Token revocation failed');
  ```

  ```python Python theme={null}
  import requests

  response = requests.post(
      'https://api.nomba.com/v1/auth/token/revoke',
      headers={
          'Content-Type': 'application/json',
          'accountId': '<accountid>',
      },
      json={
          'clientId': '2242b79d-f2cf-4ccc-ada1-e890bd1a9f0d',
          'access_token': access_token,
      },
  )

  result = response.json()
  if result['code'] != '00':
      raise Exception('Token revocation failed')
  ```

  ```json Response theme={null}
    {
      "code": "00",
      "description": "Token revoked successfully"
    }
  ```
</CodeGroup>

## Authentication Best Practices

To keep your integration secure, follow these best practices:

* Never expose credentials (`client_id`, `client_secret`, `refresh_token`) in frontend code or public repositories.

* Use secure storage for tokens in your backend (e.g., environment variables, encrypted storage).

* Refresh tokens proactively (5 minutes before expiry) instead of waiting until the last moment.

* Revoke tokens immediately if you suspect they've been leaked or compromised.

* Rotate credentials periodically and remove unused API keys.


> ## Documentation Index
> Fetch the complete documentation index at: https://developer.nomba.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Initialize Charge

> Learn how to build a customized checkout with the charge API.

<Note>
  This section of the documentation provides brief information on how to initiate and complete a charge using the Nomba API. To get the complete API, see [API reference](/nomba-api-reference/charge/get-order-details-based-on-the-generated-order-reference).
</Note>

## Use case

Nomba Charge allows you to build a customized payment experience for your users rather than using the Nomba Checkout. Typically when you create a checkout order, you will get a checkoutLink  . This will then be used to complete your payment.

Instead of redirecting your users to the checkout page to complete their payment. We expose some of the tools that power our checkout, giving you a bit of control of the payment flow. You therefore want to have your own branded checkout, improve user experience and collect card information. All of this is possible when you build a wrapper around the charge API.

## Quick Action

<CardGroup cols={2}>
  <Card title="Create a checkout order" icon="cart-shopping" href="/nomba-api-reference/online-checkout/create-an-online-checkout-order">
    Accept card and bank transfer payments.
  </Card>

  <Card title="Submit customer card details" icon="credit-card" href="/nomba-api-reference/charge/submit-customer-card-details">
    Learn how to submit customers card details
  </Card>

  <Card title="Confirm card OTP" icon="comment-dollar" href="/nomba-api-reference/charge/submit-customer-card-otp">
    Learn how to confirm the payment OTP sent to the customer’s phones.
  </Card>

  <Card title="Test Card" icon="money-check" href="/docs/api-basics/testing">
    Get Nomba test card for testing purposes.
  </Card>
</CardGroup>

## Charge Sequence Flow Diagram

When building with Nomba Charge, there are a few things to expect in terms of how it should work. The payment process has been exposed to give you more control. This means that you will do more work by collecting card information, providing device information for 3D secure authentication, and ensuring that the paying customer is the legitimate person using OTP sent to their phone. These are the listed process below to get started.

1. Create online checkout order
2. Submit user card details
3. Verify OTP to complete payment
4. Request to save user card information
5. Use Flash Account option for bank Transfer
6. Verify Transaction Status
7. Cancel Checkout Transaction

<Frame caption="Nomba Charge Sequence flow">
  <img src="https://mintcdn.com/nombainc/VJp6uGRaVI4ms-qk/images/charge-sequence-flow.png?fit=max&auto=format&n=VJp6uGRaVI4ms-qk&q=85&s=1280689e3044288e365288339d001703" style={{ borderRadius: '0.5rem' }} loading="lazy" width="569" height="880" data-path="images/charge-sequence-flow.png" />
</Frame>

## How it works

To initialize a payment, make a `POST` request to `/checkout/order` ([Create checkout order](/nomba-api-reference/online-checkout/create-an-online-checkout-order)).
`checkoutLink` and `orderReference` are returned as part of the response body. Your  `orderReference` can be use to verify transaction status or start a charge process.

Once the **checkout order** is created, the next step is to **submit the user's card details**. The customer enters their card information, which is securely processed for payment authorization. If the card details are submitted successfully, the system triggers an **OTP verification to enhance security**. To proceed, you need to verify the OTP to complete the payment by capturing the customer's OTP input and validating it. If the OTP is incorrect or timeout, provide an option to **resend it for verification**.

If the customer prefers, they can choose to **save their card information for future transactions**. Before storing the card details, an additional **OTP verification** is required to ensure security. If the customer consents and the OTP is successfully validated, the card details are securely saved. As an alternative to card payments, customers may opt to use the **Flash account option** for a bank transfer. In this case, the system returns a unique Flash account number that the customer can use to complete the payment via bank transfer.

After processing the payment, it is important to verify the transaction status. Use the `orderReference` to check the transaction status. If necessary, **fetch transaction details** from the system to provide real-time updates to the customer. In cases where the customer decides not to proceed, they can choose to **cancel the checkout transaction**. To do this, send a request to the cancellation API to terminate the transaction and prevent further processing.




> ## Documentation Index
> Fetch the complete documentation index at: https://developer.nomba.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Webhooks

> Learn how to interact with Nomba webhooks

## Overview

Webhooks allow your system to establish a communication channel with Nomba, usually via a public URL. When a payment event occurs on your account, Nomba will send a notification via this communication channel to notify you about this event.

Nomba will send a `POST`request to the public webhook URL containing the details of the event and header strictly for verifying that the webhook event originated from the Nomba system.

<Frame caption="Established webhook process flow">
  <img src="https://mintcdn.com/nombainc/VJp6uGRaVI4ms-qk/images/webhooks-1.png?fit=max&auto=format&n=VJp6uGRaVI4ms-qk&q=85&s=c18464f1d20d805a721f4748591b76bc" style={{ borderRadius: "0.5rem" }} loading="lazy" width="3840" height="3422" data-path="images/webhooks-1.png" />
</Frame>

This image shows an established communication via webhook URL between your system and Nomba.

<Note>
  It is good to note that, you must subscribe for the event type you want to get
  notified on.
</Note>

## Set up webhook event

To set up your webhooks, navigate to 'Developer' and click on 'Webhook Setup'. On this page you can set a live or test webhook URL and signature key. When you add a webhook URL, you can subscribe for the event you want to get notified on.

<Frame caption="Set up webhook on your dashboard">
  <img src="https://mintcdn.com/nombainc/dHZLqglLk2ofl5Fe/images/Webhook-setup.png?fit=max&auto=format&n=dHZLqglLk2ofl5Fe&q=85&s=79889c0b8312deaa1a5ac7fdd7765a45" style={{ borderRadius: "0.5rem" }} loading="lazy" width="2876" height="1716" data-path="images/Webhook-setup.png" />
</Frame>

<Note>
  Kindly ensure that your webhook URL is publicly available.
</Note>

## Supported Events

* **Payment Success** `payment_success` : Triggered when a payment is successfully credited to your Nomba account, e.g., Card transactions, Virtual account payments or  PayByTransfer.

* **Payout Success**  `payout_success` : Triggered when a payment is successfully debited from your account, e.g., funds transfer, bill payment.

* **Payment Failed** `payment_failed` : Triggered when a proposed payment attempt fails.

* **Payment Reversal**  `payment_reversal` : Triggered when a payment is reversed from your account back to the customer’s account.

* **Payout Failed**  `payout_failed` : Triggered when a payout transaction fails to process successfully and is not completed.

* **Payout Refund** `payout_refund` : Triggered when a payout is refunded back to your Nomba account.

### Webhook headers

Every webhook notification from Nomba includes special headers and a payload that matches the content of all supported event types. These headers will help you verify and process the request to ensure that it’s coming from Nomba, as a public URL can be accessed by anyone, so it’s to verify that all webhooks are from Nomba before giving value to your customers.

A typical webhook payload will come with the following Nomba-specific headers:

```http theme={null}
nomba-signature: 0zzATkAuEta5kpKVCExReupW/XglCk/re51P4jiDJ9c=
nomba-sig-value: 0zzATkAuEta5kpKVCExReupW/XglCk/re51P4jiDJ9c=
nomba-signature-algorithm: HmacSHA256
nomba-signature-version: 1.0.0
nomba-timestamp: 2023-03-31T05:56:47Z

```

| Header                      | Description                                                                                                             |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `nomba-signature`           | A signature created using the signature key configured while creating the webhook on the Nomba dashboard                |
| `nomba-signature-algorithm` | The algorithm used to generate the signature. Value is always `HmacSHA256`                                              |
| `nomba-signature-version`   | The version of the signature used. Value is `1.0.0` at the moment. It will keep updating as the signing process updates |
| `nomba-timestamp`           | An `RFC-3339` timestamp that identifies when the payload was sent.                                                      |

<Tip>
  * The RFC-3339 format specifies that dates should be represented using the year,
    month, and day, separated by hyphens, followed by a "T" to separate the date
    from the time, and then the time represented in hours, minutes, and seconds,
    separated by colons, with an optional fractional second component. Example;
    2022-01-01T15:45:22Z
  * HTTP header names are case insensitive. Your client should convert all header
    names to a standardized lowercase or uppercase format before trying to
    determine the value of a header.
</Tip>

Since webhooks are simply HTTP POST requests, there’s a chance that malicious actors could try to send fake webhook events to your server. To protect you from this, Nomba signs each webhook payload using the signature key you set when creating the webhook. The generated signature is included in the request headers, so your server can verify that the request truly came from Nomba and not an attacker.

<Warning>
  We recommend configuring the signature key while creating a webhook URL. While
  this configuration is optional, it is important to configure the keys and
  verify the signature of the payloads in order to prevent DDoS or
  Man-in-the-Middle attacks.
</Warning>

### Webhook payload

The content of the payload is a JSON object and it gives details about the event that has been triggered.

| Field        | Type          | Description                                              |
| ------------ | ------------- | -------------------------------------------------------- |
| `event_type` | String        | The event type that was triggered                        |
| `request_id` | String (UUID) | A unique request identifier useful for tracking messages |
| `data`       | Object (JSON) | An object describing the details of the triggered event  |

<CodeGroup>
  ```json expandable Payment Success  theme={null}
  {
    "event_type": "payment_success",
    "requestId": "49e11b44-909b-4f83-82b4-9a83aXXXXXX",
    "data": {
      "merchant": {
        "walletId": "693e907aad9ea59616XXXX",
        "walletBalance": 539.4,
        "userId": "613bb620-c8e5-45f6-9c00-XXXXXXXX"
      },
      "terminal": {},
      "transaction": {
        "aliasAccountNumber": "967913XXX",
        "fee": 0.6,
        "sessionId": "1000042602061021531516XXXXXX",
        "type": "vact_transfer",
        "transactionId": "API-VACT_TRA-613BB-eeae578a-cdd4-459c-8bd5-XXXXXX",
        "aliasAccountName": "Peter/Peter Enterprise",
        "responseCode": "",
        "originatingFrom": "api",
        "transactionAmount": 120,
        "narration": "Transfer from JOHN GRASS",
        "time": "2026-02-06T10:21:56Z",
        "aliasAccountReference": "122320250916PM",
        "aliasAccountType": "VIRTUAL"
      },
      "customer": {
        "bankCode": "305",
        "senderName": "JOHN GRASS",
        "bankName": "Paycom (Opay)",
        "accountNumber": "81689XXX"
      }
    }
  }
  ```

  ```json expandable Payout Success theme={null}
  {
    "event_type": "payout_success",
    "requestId": "76a7df87-4819-493c-90ee-XXXXXXX",
    "data": {
      "merchant": {
        "walletId": "693e907aad9ea59XXXXX",
        "walletBalance": 420,
        "userId": "613bb620-c8e5-45f6-9c00-XXXXXXXX"
      },
      "terminal": {},
      "transaction": {
        "fee": 20,
        "sessionId": "09FG260206111644XXXXXX",
        "type": "transfer",
        "transactionId": "API-TRANSFER-057A0-21e353c0-4168-4275-8355-XXXXXX",
        "responseCode": "",
        "originatingFrom": "api",
        "merchantTxRef": "20260212130PM",
        "transactionAmount": 50,
        "narration": "For API Test ",
        "time": "2026-02-06T10:16:30Z"
      },
      "customer": {
        "bankCode": "011",
        "senderName": "Peter Okins",
        "recipientName": "JOHN GRASS",
        "bankName": "First Bank of Nigeria",
        "accountNumber": "31107XXXX"
      }
    }
  }
  ```

  ```json expandable Payment Failed theme={null}
  {
      "event_type": "payment_failed",
      "requestId": "7b28d6d1-f91e-46c3-b312-89e9XXXXXXX",
      "data": {
          "merchant": {
              "userId": "usr_71kd89e9XXXXXXX"
          },
          "terminal": {
              "terminalLabel": "IKEJA MALL",
              "terminalId": "3PLQXXX"
          },
          "transaction": {
              "fee": 150,
              "type": "purchase",
              "transactionId": "POS-PURCHASE-71KD9-ae67-91fe-4b6a-a45b-689e9XXXXXXX",
              "responseCodeMessage": "Insufficient Funds",
              "rrn": "2510089e9XXXXXXX5",
              "cardIssuer": "MASTERCARD",
              "responseCode": "51",
              "originatingFrom": "pos",
              "terminalSerialNumber": "91230989e9XXXXXXX",
              "cardBank": "058",
              "transactionAmount": 25000,
              "time": "2025-10-06T17:38:45Z"
          },
          "customer": {
              "productId": "058",
              "cardPan": "539983 **** **** 4297"
          }
      }
  }
  ```

  ```json expandable Payout Refund theme={null}
  {
      "event_type": "payout_refund",
      "requestId": "062bbb0f-ecaa-481a-9ae5-12f73fXXXXXX",
      "data": {
          "merchant": {
              "walletId": "67khagklfXXXXXX",
              "walletBalance": 45000,
              "userId": "e5e6987d-32ea-4d04-8c49-13fXXXXXX"
          },
          "terminal": {},
          "transaction": {
              "fee": 7,
              "sessionId": "090645251008183142932001fXXXXXX",
              "type": "transfer",
              "transactionId": "API-TRANSFER-9772C-bf28b3d1-e18f-4ecd-a33c-4fXXXXXX",
              "responseCode": "",
              "originatingFrom": "api",
              "merchantTxRef": "5TDL0CL7CP",
              "transactionAmount": 45000,
              "narration": "From Bidemi O",
              "time": "2025-10-08T19:00:33Z"
          },
          "customer": {
              "bankCode": "327",
              "senderName": "Test",
              "recipientName": "Test Technology Limited - MAKANJU FEMI",
              "bankName": "Paga",
              "accountNumber": "07937890XX"
          }
      }
  } 
  ```
</CodeGroup>

## Webhook signature verification

To make sure a webhook truly comes from Nomba and hasn’t been altered, each request we send includes a signature in the header. This signature is generated using your webhook payload and the secret key you set on your dashboard.

On your end, verification is straightforward:

1. **Re-create the signature** :
   Use the same secret key and payload to generate a hash - HMAC signature.

2. **Compare signatures** :
   Match your generated hash with the nomba-signature header we sent. If they’re the same, you can trust the webhook.

The tab below contains sample code demonstrating how to calculate the HMAC signature and compare it with the signature sent via the webhook.

<Tabs>
  <Tab title="GoLang">
    ```go expandable CalculateHMAC.go theme={null}
          package main

          import (
              "crypto/hmac"
              "crypto/sha256"
              "encoding/base64"
              "encoding/json"
              "fmt"
              "log"
              "strings"
          )

          // --- Struct Definitions for JSON Mapping ---

          type Payload struct {
              EventType string `json:"event_type"`
              RequestID string `json:"requestId"`
              Data      Data   `json:"data"`
          }

          type Data struct {
              Merchant    Merchant    `json:"merchant"`
              Terminal    map[string]interface{} `json:"terminal"`
              Transaction Transaction `json:"transaction"`
              Customer    Customer    `json:"customer"`
          }

          type Merchant struct {
              WalletID       string  `json:"walletId"`
              WalletBalance  float64 `json:"walletBalance"`
              UserID         string  `json:"userId"`
          }

          type Transaction struct {
              AliasAccountNumber   string  `json:"aliasAccountNumber"`
              Fee                  float64 `json:"fee"`
              SessionID            string  `json:"sessionId"`
              Type                 string  `json:"type"`
              TransactionID        string  `json:"transactionId"`
              AliasAccountName     string  `json:"aliasAccountName"`
              ResponseCode         string  `json:"responseCode"`
              OriginatingFrom      string  `json:"originatingFrom"`
              TransactionAmount    float64 `json:"transactionAmount"`
              Narration            string  `json:"narration"`
              Time                 string  `json:"time"`
              AliasAccountReference string `json:"aliasAccountReference"`
              AliasAccountType     string  `json:"aliasAccountType"`
          }

          type Customer struct {
              BankCode     string `json:"bankCode"`
              SenderName   string `json:"senderName"`
              BankName     string `json:"bankName"`
              AccountNumber string `json:"accountNumber"`
          }

          // --- Core Logic ---

          func main() {
              hooksCron2()
          }

          func hooksCron2() {
              payloadJSON := `
              {
              "event_type": "payment_success",
              "requestId": "45f2dc2d-d559-4773-bba3-2d5ec17b2e20",
              "data": {
                  "merchant": {
                  "walletId": "6756ff80aafe04a795f18b38",
                  "walletBalance": 6052,
                  "userId": "b7b10e81-e57d-41d0-8fdc-f4e23a132bbf"
                  },
                  "terminal": {},
                  "transaction": {
                  "aliasAccountNumber": "5343270516",
                  "fee": 5,
                  "sessionId": "IFAP-TRANSFER-46501-e0339485-1a2f-4b43-9bd5-fec9649e5928",
                  "type": "vact_transfer",
                  "transactionId": "API-VACT_TRA-B7B10-0435b274-807a-4bc7-8abe-9dbb4548fd7a",
                  "aliasAccountName": "ZAXBOX/EZENNA NWACHUKWU",
                  "responseCode": "",
                  "originatingFrom": "api",
                  "transactionAmount": 10,
                  "narration": "Habiblahi Hamzat Transfer 10.00 To ZAXBOX/EZENNA NWACHUKWU - Nomba",
                  "time": "2025-09-29T10:51:44Z",
                  "aliasAccountReference": "654f7c80bd4a510c90fb7f92",
                  "aliasAccountType": "VIRTUAL"
                  },
                  "customer": {
                  "bankCode": "090645",
                  "senderName": "Habiblahi Hamzat",
                  "bankName": "Nombank",
                  "accountNumber": "9617811496"
                  }
              }
              }`

              signatureValue := "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw="
              nombaTimeStamp := "2025-09-29T10:51:44Z"
              secret := "HkatexKDZg7CLWy96q5sfrVHSvtoz92B"

              mySig, err := generateSignature(payloadJSON, secret, nombaTimeStamp)
              if err != nil {
                  log.Fatalf("Error generating signature: %v", err)
              }

              log.Printf("Generated signature [%s]", mySig)
              log.Printf("Expected signature [%s]", signatureValue)

              if strings.EqualFold(signatureValue, mySig) {
                  log.Println(">>>>>>> Signatures match <<<<<<<<<")
              } else {
                  log.Println("<<<<<<<<< Signatures did not match >>>>>>>>>")
              }
          }

          func generateSignature(payloadJSON, secret, timeStamp string) (string, error) {
              var payload Payload
              if err := json.Unmarshal([]byte(payloadJSON), &payload); err != nil {
                  return "", fmt.Errorf("error parsing JSON payload: %w", err)
              }

              transaction := payload.Data.Transaction
              merchant := payload.Data.Merchant

              transactionResponseCode := transaction.ResponseCode
              if transactionResponseCode == "null" {
                  transactionResponseCode = ""
              }

              // Construct the exact signature payload as in Java
              hashingPayload := fmt.Sprintf(
                  "%s:%s:%s:%s:%s:%s:%s:%s:%s",
                  payload.EventType,
                  payload.RequestID,
                  merchant.UserID,
                  merchant.WalletID,
                  transaction.TransactionID,
                  transaction.Type,
                  transaction.Time,
                  transactionResponseCode,
                  timeStamp,
              )

              log.Printf("::: payload to hash --> [%s] :::", hashingPayload)

              // Generate HMAC SHA256 and encode Base64
              h := hmac.New(sha256.New, []byte(secret))
              h.Write([]byte(hashingPayload))
              hash := h.Sum(nil)

              return base64.StdEncoding.EncodeToString(hash), nil
          }
    ```
  </Tab>

  <Tab title="Python">
    ```python expandable CalculateHMAC.py theme={null}
        import json
        import hmac
        import hashlib
        import base64
        import logging

        logging.basicConfig(level=logging.INFO, format="%(message)s")

        def hooks_cron2():
            try:
                payload = """
                {
                "event_type": "payment_success",
                "requestId": "45f2dc2d-d559-4773-bba3-2XXXXXXXXXX",
                "data": {
                    "merchant": {
                    "walletId": "6756ff80aafe04a795f18b3XXXXXXXXXX",
                    "walletBalance": 6052,
                    "userId": "b7b10e81-e57d-41d0-8XXXXXXXXXX"
                    },
                    "terminal": {},
                    "transaction": {
                    "aliasAccountNumber": "5343270516",
                    "fee": 5,
                    "sessionId": "IFAP-TRANSFER-46501-e0339485-1a2f-4b43-9bXXXXXXXXXX",
                    "type": "vact_transfer",
                    "transactionId": "API-VACT_TRA-B7B10-0435b274-807a-4bc7-8abe-9dbXXXXXXXXXX",
                    "aliasAccountName": "SAMPLE/JOHN DOE",
                    "responseCode": "",
                    "originatingFrom": "api",
                    "transactionAmount": 10,
                    "narration": "John Doe Transfer 10.00 To ZAXBOX/EZENNA NWACHUKWU - Nomba",
                    "time": "2025-09-29T10:51:44Z",
                    "aliasAccountReference": "654f7c80bd4**10c90fb7f92",
                    "aliasAccountType": "VIRTUAL"
                    },
                    "customer": {
                    "bankCode": "090645",
                    "senderName": "John Doe",
                    "bankName": "Nombank",
                    "accountNumber": "0000000000"
                    }
                }
                }
                """

                signature_value = "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw="
                nomba_timestamp = "2025-09-29T10:51:44Z"
                secret = "sampleScret"

                my_sig = generate_signature(payload, secret, nomba_timestamp)

                logging.info(f"Generated signature [{my_sig}]")
                logging.info(f"Expected signature [{signature_value}]")

                if signature_value.lower() == my_sig.lower():
                    logging.info(">>>>>>> Signatures match <<<<<<<<<")
                else:
                    logging.info("<<<<<<<<< Signatures did not match >>>>>>>>>")

            except Exception as ex:
                logging.error(f"Error occurred while generating signature: {ex}")

        def generate_signature(payload: str, secret: str, timestamp: str) -> str:
            request_payload = json.loads(payload)

            data = request_payload.get("data", {})
            merchant = data.get("merchant", {})
            transaction = data.get("transaction", {})

            event_type = request_payload.get("event_type", "")
            request_id = request_payload.get("requestId", "")
            user_id = merchant.get("userId", "")
            wallet_id = merchant.get("walletId", "")
            transaction_id = transaction.get("transactionId", "")
            transaction_type = transaction.get("type", "")
            transaction_time = transaction.get("time", "")
            transaction_response_code = transaction.get("responseCode", "")

            if transaction_response_code == "null":
                transaction_response_code = ""

            # Construct the same hashing payload as in Java/Go
            hashing_payload = f"{event_type}:{request_id}:{user_id}:{wallet_id}:{transaction_id}:{transaction_type}:{transaction_time}:{transaction_response_code}:{timestamp}"

            logging.info(f"::: payload to hash --> [{hashing_payload}] :::")

            # Compute HMAC-SHA256 and Base64 encode it
            digest = hmac.new(secret.encode(), hashing_payload.encode(), hashlib.sha256).digest()
            signature = base64.b64encode(digest).decode()

            return signature

        if __name__ == "__main__":
            hooks_cron2()
    ```
  </Tab>

  <Tab title="Javascript">
    ```javascript expandable CalculateHMAC.js theme={null}
        import crypto from "crypto";

        async function hooksCron2() {
        try {
            const payload = `
            {
            "event_type": "payment_success",
            "requestId": "45f2dc2d-d559-4773-bba3-2XXXXXXXXXX",
            "data": {
                "merchant": {
                "walletId": "6756ff80aafe04XXXXXXXXXX",
                "walletBalance": 6052,
                "userId": "b7b10e81-**-**-**-f4e23a132bbf"
                },
                "terminal": {},
                "transaction": {
                "aliasAccountNumber": "5343270516",
                "fee": 5,
                "sessionId": "IFAP-TRANSFER-46501-e0339485-1a2f-4b43-9bd5-XXXXXXXXXX",
                "type": "vact_transfer",
                "transactionId": "API-VACT_TRA-B7B10-0435b274-807a-4bc7-8abe-9XXXXXXXXXX",
                "aliasAccountName": "SAMPLE/JOHN DOE",
                "responseCode": "",
                "originatingFrom": "api",
                "transactionAmount": 10,
                "narration": "John Does Transfer 10.00 To SAMPLE/JOHN DOE - Nomba",
                "time": "2025-09-29T10:51:44Z",
                "aliasAccountReference": "sampleAccountReference",
                "aliasAccountType": "VIRTUAL"
                },
                "customer": {
                "bankCode": "090645",
                "senderName": "John Does",
                "bankName": "Nombank",
                "accountNumber": "0000000000"
                }
            }
            }`;

            const signatureValue = "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw=";
            const nombaTimeStamp = "2025-09-29T10:51:44Z";
            const secret = "sampleSecret";

            const mySig = generateSignature(payload, secret, nombaTimeStamp);

            console.log(`Generated signature [${mySig}]`);
            console.log(`Expected signature [${signatureValue}]`);

            if (signatureValue.toLowerCase() === mySig.toLowerCase()) {
            console.log(">>>>>>> Signatures match <<<<<<<<<<<");
            } else {
            console.log("<<<<<<<<< Signatures did not match >>>>>>>>>");
            }
        } catch (ex) {
            console.error("Error occurred while generating signature:", ex.message);
        }
        }

        function generateSignature(payload, secret, timeStamp) {
        const requestPayload = JSON.parse(payload);
        const data = requestPayload.data || {};
        const merchant = data.merchant || {};
        const transaction = data.transaction || {};

        const eventType = requestPayload.event_type || "";
        const requestId = requestPayload.requestId || "";
        const userId = merchant.userId || "";
        const walletId = merchant.walletId || "";
        const transactionId = transaction.transactionId || "";
        const transactionType = transaction.type || "";
        const transactionTime = transaction.time || "";
        let transactionResponseCode = transaction.responseCode || "";

        if (transactionResponseCode === "null") {
            transactionResponseCode = "";
        }


        const hashingPayload = `${eventType}:${requestId}:${userId}:${walletId}:${transactionId}:${transactionType}:${transactionTime}:${transactionResponseCode}:${timeStamp}`;

        console.log(`::: payload to hash --> [${hashingPayload}] :::`);

        const hmac = crypto.createHmac("sha256", secret);
        hmac.update(hashingPayload);
        const hash = hmac.digest("base64");

        return hash;
        }

        // Run
        hooksCron2();
    ```
  </Tab>

  <Tab title="Java">
    ```java expandable CalculateHMAC.java theme={null}
    import com.fasterxml.jackson.annotation.JsonProperty;
    import com.fasterxml.jackson.core.JsonProcessingException;
    import com.fasterxml.jackson.databind.ObjectMapper;
    import lombok.Data;
    import lombok.extern.slf4j.Slf4j;

    import javax.crypto.Mac;
    import javax.crypto.spec.SecretKeySpec;
    import java.util.Base64;

    @Slf4j
    public class NombaHooksRefactored {

        private static final ObjectMapper objectMapper = new ObjectMapper();

        public static void main(String[] args) throws Exception {
            new NombaHooksRefactored().hooksCron2();
        }

        public void hooksCron2() {
            try {
                String payload = """
                    {
                    "event_type": "payment_success",
                    "requestId": "45f2dc2d-d559-4773-bba3-2XXXXXXXXXX",
                    "data": {
                        "merchant": {
                        "walletId": "6756ff80aafe04aXXXXXXXXXX",
                        "walletBalance": 6052,
                        "userId": "b7b10e81-**-**-**-f4e23a132bbf"
                        },
                        "terminal": {},
                        "transaction": {
                        "aliasAccountNumber": "5343270516",
                        "fee": 5,
                        "sessionId": "IFAP-TRANSFER-46501-***-1a2f-4b43-9bd5-fec964XXXXXXXXXX28",
                        "type": "vact_transfer",
                        "transactionId": "API-VACT_TRA-B7B10-0435b274-807a-4bc7-8XXXXXXXXXX",
                        "aliasAccountName": "SAMPLE/JOHN DOE",
                        "responseCode": "",
                        "originatingFrom": "api",
                        "transactionAmount": 10,
                        "narration": "John Doe Transfer 10.00 To ZAXBOX/EZENNA NWACHUKWU - Nomba",
                        "time": "2025-09-29T10:51:44Z",
                        "aliasAccountReference": "654f7c80bd4***0c90fb7f92",
                        "aliasAccountType": "VIRTUAL"
                        },
                        "customer": {
                        "bankCode": "090645",
                        "senderName": "John Doe",
                        "bankName": "Nombank",
                        "accountNumber": "0000000000"
                        }
                    }
                    }
                    """;

                String signatureValue = "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw=";
                String nombaTimeStamp = "2025-09-29T10:51:44Z";
                String secret = "HkatexKDZg7CLWy96q5sfrVHSvtXXXXXXXXXXB";

                HookPayload hookPayload = objectMapper.readValue(payload, HookPayload.class);

                String mySig = generateSignature(hookPayload, secret, nombaTimeStamp);

                log.info("Generated signature [{}]", mySig);
                log.info("Expected signature [{}]", signatureValue);

                if (signatureValue.equalsIgnoreCase(mySig)) {
                    log.info(">>>>>>> Signatures match <<<<<<<<<");
                } else {
                    log.info("<<<<<<<<< Signatures did not match >>>>>>>>>");
                }

            } catch (Exception ex) {
                log.error("Error occurred while generating signature. Error message [{}]", ex.getMessage(), ex);
            }
        }

        public String generateSignature(HookPayload payload, String secret, String timeStamp) throws Exception {
            var data = payload.getData();
            var merchant = data.getMerchant();
            var transaction = data.getTransaction();

            String eventType = safe(payload.getEventType());
            String requestId = safe(payload.getRequestId());
            String userId = safe(merchant.getUserId());
            String walletId = safe(merchant.getWalletId());
            String transactionId = safe(transaction.getTransactionId());
            String transactionType = safe(transaction.getType());
            String transactionTime = safe(transaction.getTime());
            String transactionResponseCode = safe(transaction.getResponseCode());

            if ("null".equalsIgnoreCase(transactionResponseCode)) {
                transactionResponseCode = "";
            }

            String hashingPayload = String.format(
                    "%s:%s:%s:%s:%s:%s:%s:%s:%s",
                    eventType, requestId, userId, walletId,
                    transactionId, transactionType, transactionTime,
                    transactionResponseCode, timeStamp
            );

            log.info("::: payload to hash --> [{}] :::", hashingPayload);

            Mac sha256HMAC = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKey = new SecretKeySpec(secret.getBytes(), "HmacSHA256");
            sha256HMAC.init(secretKey);

            byte[] hash = sha256HMAC.doFinal(hashingPayload.getBytes());
            return Base64.getEncoder().encodeToString(hash);
        }

        private String safe(String value) {
            return value == null ? "" : value;
        }
    }

    // POJO Models (Strongly Typed Payload Classes)

    import com.fasterxml.jackson.annotation.JsonProperty;
    import lombok.Data;

    @Data
    public class HookPayload {
        @JsonProperty("event_type")
        private String eventType;

        @JsonProperty("requestId")
        private String requestId;

        @JsonProperty("data")
        private HookData data;
    }

    @Data
    class HookData {
        private Merchant merchant;
        private Transaction transaction;
        private Customer customer;
        private Object terminal;
    }

    @Data
    class Merchant {
        private String walletId;
        private Double walletBalance;
        private String userId;
    }

    @Data
    class Transaction {
        private String transactionId;
        private String type;
        private String time;
        private String responseCode;
    }

    @Data
    class Customer {
        private String bankCode;
        private String senderName;
        private String bankName;
        private String accountNumber;
    }
    ```
  </Tab>

  <Tab title="C#">
    ```csharp expandable CalculateHMAC.cs theme={null}
        using System;
        using System.Text;
        using System.Text.Json;
        using System.Text.Json.Serialization;
        using System.Security.Cryptography;

        public class HooksCron
        {
            public static void Main()
            {
                try
                {
                    var payload = @"
                    {
                    ""event_type"": ""payment_success"",
                    ""requestId"": ""45f2dc2d-d559-4773-bba3-2XXXXXXXXXX"",
                    ""data"": {
                        ""merchant"": {
                        ""walletId"": ""6756ff80aafe04a7XXXXXXXXXX"",
                        ""walletBalance"": 6052,
                        ""userId"": ""b7b10e81-e57d-41d0-8fdc-f4XXXXXXXXXX""
                        },
                        ""terminal"": {},
                        ""transaction"": {
                        ""aliasAccountNumber"": ""5343270516"",
                        ""fee"": 5,
                        ""sessionId"": ""IFAP-TRANSFER-46501-e0339485-1a2f-4b43-9bd5-feXXXXXXXXXX28"",
                        ""type"": ""vact_transfer"",
                        ""transactionId"": ""API-VACT_TRA-B7B10-0435b274-807a-4bc7-8abe-XXXXXXXXXXd7a"",
                        ""aliasAccountName"": ""ZAXBOX/EZENNA NWACHUKWU"",
                        ""responseCode"": """",
                        ""originatingFrom"": ""api"",
                        ""transactionAmount"": 10,
                        ""narration"": ""Habiblahi Hamzat Transfer 10.00 To ZAXBOX/EZENNA NWACHUKWU - Nomba"",
                        ""time"": ""2025-09-29T10:51:44Z"",
                        ""aliasAccountReference"": ""654XXXXXXXXXX92"",
                        ""aliasAccountType"": ""VIRTUAL""
                        },
                        ""customer"": {
                        ""bankCode"": ""090645"",
                        ""senderName"": ""Habiblahi Hamzat"",
                        ""bankName"": ""Nombank"",
                        ""accountNumber"": ""9617811496""
                        }
                    }
                    }";

                    var signatureValue = "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw=";
                    var nombaTimestamp = "2025-09-29T10:51:44Z";
                    var secret = "HkatexKDZg7CLWy96q5sfrVH92B";

                    // Deserialize payload into object model
                    var requestPayload = JsonSerializer.Deserialize<HookPayload>(payload);

                    var mySig = GenerateSignature(requestPayload, secret, nombaTimestamp);

                    Console.WriteLine($"Generated signature [{mySig}]");
                    Console.WriteLine($"Expected signature [{signatureValue}]");

                    if (string.Equals(signatureValue, mySig, StringComparison.OrdinalIgnoreCase))
                    {
                        Console.WriteLine(">>>>>>> Signatures match <<<<<<<<<");
                    }
                    else
                    {
                        Console.WriteLine("<<<<<<<<< Signatures did not match >>>>>>>>>");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error occurred while generating signature. Error: {ex.Message}");
                }
            }

            public static string GenerateSignature(HookPayload payload, string secret, string timestamp)
            {
                var data = payload.Data;
                var merchant = data.Merchant;
                var transaction = data.Transaction;

                string eventType = payload.EventType ?? "";
                string requestId = payload.RequestId ?? "";
                string userId = merchant?.UserId ?? "";
                string walletId = merchant?.WalletId ?? "";
                string transactionId = transaction?.TransactionId ?? "";
                string transactionType = transaction?.Type ?? "";
                string transactionTime = transaction?.Time ?? "";
                string transactionResponseCode = transaction?.ResponseCode ?? "";

                if (transactionResponseCode == "null")
                {
                    transactionResponseCode = "";
                }

                var hashingPayload = $"{eventType}:{requestId}:{userId}:{walletId}:{transactionId}:{transactionType}:{transactionTime}:{transactionResponseCode}:{timestamp}";
                Console.WriteLine($"::: payload to hash --> [{hashingPayload}] :::");

                using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(secret));
                var hash = hmac.ComputeHash(Encoding.UTF8.GetBytes(hashingPayload));
                var signature = Convert.ToBase64String(hash);

                return signature;
            }
        }

        #region Models

        public class HookPayload
        {
            [JsonPropertyName("event_type")]
            public string? EventType { get; set; }

            [JsonPropertyName("requestId")]
            public string? RequestId { get; set; }

            [JsonPropertyName("data")]
            public HookData Data { get; set; } = new();
        }

        public class HookData
        {
            [JsonPropertyName("merchant")]
            public Merchant? Merchant { get; set; }

            [JsonPropertyName("transaction")]
            public Transaction? Transaction { get; set; }

            [JsonPropertyName("customer")]
            public Customer? Customer { get; set; }

            [JsonPropertyName("terminal")]
            public object? Terminal { get; set; }
        }

        public class Merchant
        {
            [JsonPropertyName("walletId")]
            public string? WalletId { get; set; }

            [JsonPropertyName("walletBalance")]
            public decimal? WalletBalance { get; set; }

            [JsonPropertyName("userId")]
            public string? UserId { get; set; }
        }

        public class Transaction
        {
            [JsonPropertyName("transactionId")]
            public string? TransactionId { get; set; }

            [JsonPropertyName("type")]
            public string? Type { get; set; }

            [JsonPropertyName("time")]
            public string? Time { get; set; }

            [JsonPropertyName("responseCode")]
            public string? ResponseCode { get; set; }
        }

        public class Customer
        {
            [JsonPropertyName("bankCode")]
            public string? BankCode { get; set; }

            [JsonPropertyName("senderName")]
            public string? SenderName { get; set; }

            [JsonPropertyName("bankName")]
            public string? BankName { get; set; }

            [JsonPropertyName("accountNumber")]
            public string? AccountNumber { get; set; }
        }

        #endregion     
    ```
  </Tab>

  <Tab title="php">
    <Note>
      This code samples is supported in php
    </Note>

    ```php expandable CalculateHMAC.php theme={null}
        <?php

        function hooksCron2() {
            try {
                $payload = <<<JSON
                {
                "event_type": "payment_success",
                "requestId": "45f2dc2d-d559-4773-bba3-2XXXXXXXXXX",
                "data": {
                    "merchant": {
                    "walletId": "6756ff80aafe04a7XXXXXXXXXX",
                    "walletBalance": 6052,
                    "userId": "b7b10e81-***-41d0-***-f4e23a132bbf"
                    },
                    "terminal": {},
                    "transaction": {
                    "aliasAccountNumber": "5343270516",
                    "fee": 5,
                    "sessionId": "IFAP-TRANSFER-46501-e0339485-1a2f-4b43-9bd5-XXXXXXXXXX8",
                    "type": "vact_transfer",
                    "transactionId": "API-VACT_TRA-B7B10-0435b274-807a-4bc7-8abe-XXXXXXXXXX",
                    "aliasAccountName": "SAMPLE/JOHN DOE",
                    "responseCode": "",
                    "originatingFrom": "api",
                    "transactionAmount": 10,
                    "narration": "Joh Doe Transfer 10.00 To SAMPLE/JOHN DOE - Nomba",
                    "time": "2025-09-29T10:51:44Z",
                    "aliasAccountReference": "654f7c80b****510c90f***2",
                    "aliasAccountType": "VIRTUAL"
                    },
                    "customer": {
                    "bankCode": "090645",
                    "senderName": "John Doe",
                    "bankName": "Nombank",
                    "accountNumber": "0000000000"
                    }
                }
                }
                JSON;

                $signatureValue = "Kt9095hQxfgmVbx6iz7G2tPhHdbdXgLlyY/mf35sptw=";
                $nombaTimeStamp = "2025-09-29T10:51:44Z";
                $secret = "SampleSecret";

                $mySig = generateSignature($payload, $secret, $nombaTimeStamp);

                echo "Generated signature [{$mySig}]\n";
                echo "Expected signature [{$signatureValue}]\n";

                if (strcasecmp($signatureValue, $mySig) === 0) {
                    echo ">>>>>>> Signatures match <<<<<<<<<\n";
                } else {
                    echo "<<<<<<<<< Signatures did not match >>>>>>>>>\n";
                }
            } catch (Exception $ex) {
                echo "Error occurred while generating signature: {$ex->getMessage()}\n";
            }
        }

        function generateSignature($payload, $secret, $timeStamp) {
            $requestPayload = json_decode($payload, true);

            $data = $requestPayload['data'] ?? [];
            $merchant = $data['merchant'] ?? [];
            $transaction = $data['transaction'] ?? [];

            $eventType = $requestPayload['event_type'] ?? '';
            $requestId = $requestPayload['requestId'] ?? '';
            $userId = $merchant['userId'] ?? '';
            $walletId = $merchant['walletId'] ?? '';
            $transactionId = $transaction['transactionId'] ?? '';
            $transactionType = $transaction['type'] ?? '';
            $transactionTime = $transaction['time'] ?? '';
            $transactionResponseCode = $transaction['responseCode'] ?? '';

            if ($transactionResponseCode === "null") {
                $transactionResponseCode = '';
            }

            // Construct payload string same as Java's String.format(SIG_FORMAT, data, timeStamp)
            $hashingPayload = sprintf(
                "%s:%s:%s:%s:%s:%s:%s:%s:%s",
                $eventType,
                $requestId,
                $userId,
                $walletId,
                $transactionId,
                $transactionType,
                $transactionTime,
                $transactionResponseCode,
                $timeStamp
            );

            echo "::: payload to hash --> [{$hashingPayload}] :::\n";

            // Generate HMAC SHA256 and encode in Base64
            $hash = hash_hmac('sha256', $hashingPayload, $secret, true);
            return base64_encode($hash);
        }

        // Run
        hooksCron2();
    ```
  </Tab>
</Tabs>

## Idempotency in Nomba

Nomba allows you to pass an idempotency key using the `X-Idempotent-key` header. This helps prevent duplicate requests when the first request fails due to issues like network interruptions.

Although our system already handles idempotency internally, we recommend that you include an idempotency key when calling endpoints such as Bank Transfer.

For example, if a bank transfer request succeeds but the confirmation is lost, resending the same request with the same idempotency key ensures that:

* Only the first request is processed.

* A duplicate request will either return the original response if identical or throw an error if different.

This keeps your transactions safe and predictable by avoiding accidental duplicate transfers.

<Warning>
  Always use a unique idempotency key for each request. This is best practice to ensure consistent behavior.
</Warning>

The following examples show how to generate a unique keys in popular programming languages.

<CodeGroup>
  ```go unique_key.go theme={null}
  package main

  import (
  	"fmt"
  	"github.com/google/uuid"
  )

  func main() {
  	idempotentKey := uuid.New().String()
  	fmt.Println(idempotentKey)
  }
  ```

  ```javascript unique_key.js theme={null}
  const { v4: uuidv4 } = require('uuid');
  const idempotentKey = uuidv4();
  console.log(idempotentKey);
  ```

  ```python unique_key.py theme={null}
  import uuid
  idempotent_key = str(uuid.uuid4())
  print(idempotent_key)
  ```

  ```java unique_key.java theme={null}
  import java.util.UUID;
  String idempotentKey = UUID.randomUUID().toString();
  System.out.println(idempotentKey);
  ```

  ```cs unique_key.cs theme={null}
  using System;

  string idempotentKey = Guid.NewGuid().ToString();
  Console.WriteLine(idempotentKey);
  ```
</CodeGroup>

## Retrying Failed Webhooks

When a webhook fails to deliver because the receiving server does not return a `2XX` status code, Nomba automatically retries the request using an exponential backoff policy. This approach spaces out retries with increasing delays, preventing your server from being overwhelmed while still ensuring delivery. Both `4XX` client errors and `5XX` server errors will trigger this retry flow. After the first failed attempt, Nomba will make up to five additional attempts to re-deliver the webhook.

The table below gives proper perspective into how failed webhooks would be retried.

| No of Retries | WaitTime (in Seconds) | WaitTime (in Mins) |
| ------------- | --------------------- | ------------------ |
| 1             | `120 secs`            | `2 mins`           |
| 2             | `280 secs`            | `~ 5 mins`         |
| 3             | `640 secs`            | `~ 11 mins`        |
| 4             | `1440 secs`           | `24 mins`          |
| 5             | `3200 secs`           | `~ 53 mins`        |

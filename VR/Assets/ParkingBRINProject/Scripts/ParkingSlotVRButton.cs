using UnityEngine;
using UnityEngine.UI;
using TMPro;
using Firebase.Database;
using Firebase.Extensions;
using Firebase.Auth; 
using System.Collections;

public class ParkingSlotVRButton : MonoBehaviour
{
    [Header("Config")]
    public string slotName = "slot_1";
    public TMP_Text buttonText;

    private DatabaseReference db;
    private bool isOccupied = false;
    private string normalText = "";
    private string userFirstName = "User";  

    void Start()
    {
        db = FirebaseDatabase.DefaultInstance.RootReference;

        if (FirebaseAuth.DefaultInstance.CurrentUser != null)
        {
            string email = FirebaseAuth.DefaultInstance.CurrentUser.Email;
            if (!string.IsNullOrEmpty(email) && email.Contains("@"))
            {
                string rawName = email.Split('@')[0];
                if (!string.IsNullOrEmpty(rawName))
                {
                    userFirstName = char.ToUpper(rawName[0]) + rawName.Substring(1);
                }
            }
        }

        var btn = GetComponent<Button>();
        if (btn != null)
        {
            btn.onClick.RemoveAllListeners();
            btn.onClick.AddListener(OnButtonClick);
        }

        FirebaseDatabase.DefaultInstance
            .GetReference("slot_parking")
            .Child(slotName)
            .ValueChanged += OnSlotChanged;
    }

    void OnSlotChanged(object sender, ValueChangedEventArgs args)
    {
        if (args.DatabaseError != null || !args.Snapshot.Exists) return;

        var occNode = args.Snapshot.Child("occupied");
        if (occNode.Exists && occNode.Value != null)
        {
            string raw = occNode.Value.ToString();
            if (!bool.TryParse(raw, out isOccupied))
                isOccupied = raw.Equals("1") || raw.Equals("True") || raw.Equals("true");
        }
        else
        {
            isOccupied = false;
        }

        normalText = isOccupied
            ? $"Kosongkan Slot Parkir"
            : $"Isi Slot Parkir";

        if (buttonText != null) buttonText.text = normalText;
    }

    public void OnButtonClick()
    {
        string timestampKey = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

        string action = isOccupied ? "Kosongkan" : "Isi";
        string message = $"{action} Parkir {System.Globalization.CultureInfo.CurrentCulture.TextInfo.ToTitleCase(slotName.Replace("_", " ").ToLower())} oleh {userFirstName}";

        Debug.Log($"Sending → slot_messages_vr/{slotName}/{timestampKey}: {message}");

        db.Child("slot_messages_vr").Child(slotName).Child(timestampKey).SetValueAsync(message)
          .ContinueWithOnMainThread(t =>
          {
              if (t.IsFaulted)
              {
                  ShowTemp("Gagal mengirim pesan", 2f);
              }
              else
              {
                  ShowTemp("Pesan Berhasil Terkirim!", 2f);
              }
          });
    }

    private void ShowTemp(string temp, float seconds)
    {
        if (buttonText == null) return;
        StartCoroutine(TempRoutine(temp, seconds));
    }

    private IEnumerator TempRoutine(string temp, float seconds)
    {
        string prev = normalText;
        buttonText.text = temp;
        yield return new WaitForSeconds(seconds);
        buttonText.text = prev;
    }
}

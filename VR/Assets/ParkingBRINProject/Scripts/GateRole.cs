using UnityEngine;
using UnityEngine.UI;
using Firebase;
using Firebase.Auth;
using Firebase.Database;
using System.Collections;

public class GateRole : MonoBehaviour
{
    [Header("Gate Buttons (all 20)")]
    public GameObject[] gateButtons; 

    private FirebaseAuth auth;
    private DatabaseReference dbReference;
    private FirebaseUser user;

    void Start()
    {
        auth = FirebaseAuth.DefaultInstance;
        dbReference = FirebaseDatabase.DefaultInstance.RootReference;

        if (auth.CurrentUser != null)
        {
            user = auth.CurrentUser;
            StartCoroutine(CheckUserRole(user.UserId));
        }
    }

    IEnumerator CheckUserRole(string userId)
    {
        var roleTask = dbReference.Child("users").Child(userId).Child("role").GetValueAsync();
        yield return new WaitUntil(() => roleTask.IsCompleted);

        if (roleTask.Exception != null)
        {
            Debug.LogError(roleTask.Exception);
        }
        else if (roleTask.Result.Value != null)
        {
            string role = roleTask.Result.Value.ToString();
            UpdateGateUI(role);
        }
    }

    private void UpdateGateUI(string role)
    {
        bool canSee = (role == "Admin" || role == "Operator");

        foreach (GameObject btn in gateButtons)
        {
            if (btn != null)
                btn.SetActive(canSee);
        }
    }
}

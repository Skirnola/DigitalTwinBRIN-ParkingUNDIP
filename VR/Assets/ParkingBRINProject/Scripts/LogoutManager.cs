using UnityEngine;
using UnityEngine.SceneManagement;
using Firebase.Auth;

public class LogoutManager : MonoBehaviour
{
    private FirebaseAuth auth;

    void Start()
    {
        auth = FirebaseAuth.DefaultInstance;
    }

    public void Logout()
    {
        auth.SignOut();
        Debug.Log("User logged out.");
        SceneManager.LoadScene("LoginSignup");
    }
}

from django import forms


class PrintRequestForm(forms.Form):

    STATUS_CHOICES = (
        ('Faculty', 'Faculty'),
        ('Undergraduate Student', 'Undergraduate Student'),
        ('Graduate Student', 'Graduate Student'),
        ('Visiting Scholar', 'Visiting Scholar'),
        ('Staff Member', 'Staff Member'),
        ('Other', 'Other'),
        )

    entry_994442820 = forms.CharField(label="Title", widget=forms.HiddenInput)
    entry_1457763040 = forms.CharField(label="ISBN", widget=forms.HiddenInput)
    entry_1696606454 = forms.CharField(label="Requestor Name",
                                       required=True)
    entry_699468619 = forms.ChoiceField(label="GW Affiliation",
                                        required=True,
                                        choices=STATUS_CHOICES)
    entry_571937374 = forms.CharField(label="Course, Department, or Program",
                                      widget=forms.TextInput(attrs={'size':'40'}),
                                      required=True,
                                      help_text='Be as specific as possible.')
    entry_700519383 = forms.EmailField(label="Email Address",
                                       required=True)
    entry_1537829419 = forms.CharField(label="BIBID", widget=forms.HiddenInput)
    entry_628191412 = forms.BooleanField(label="Request book be held at Gelman Library Check Out Desk",
                                         initial=True,
                                         required=False)
    title = forms.CharField(widget=forms.HiddenInput, required=False)
    isbn = forms.CharField(widget=forms.HiddenInput, required=False)

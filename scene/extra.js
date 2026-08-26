
/* before/after reveal: the range input carries the interaction so keyboard and
   screen readers get it for free; the divider is decorative. */
(function () {
  document.querySelectorAll(".ba-stage").forEach(function (stage) {
    var input = stage.querySelector(".ba-range");
    if (!input) return;
    var apply = function () { stage.style.setProperty("--rev", input.value + "%"); };
    input.addEventListener("input", apply);
    input.addEventListener("change", apply);
    apply();
  });
})();
